""" crawlers/cls_controller.py """
from ispider_core.utils.logger import LoggerFactory
from ispider_core.utils import efiles
from ispider_core.utils import state_manager

from ispider_core.crawlers import cls_queue_out
from ispider_core.crawlers import cls_seen_filter
from ispider_core.crawlers import cls_domain_stats
from ispider_core.crawlers import thread_queue_in
from ispider_core.crawlers import thread_stats
from ispider_core.crawlers import thread_save_finished
from ispider_core.crawlers import stage_unified

from queue import LifoQueue
import multiprocessing as mp
import time
from itertools import repeat
import threading

import os
import pickle

from multiprocessing.managers import BaseManager

class MyManager(BaseManager):
    pass

class SeenFilterManager(BaseManager):
    pass
    
MyManager.register('LifoQueue', LifoQueue)
SeenFilterManager.register('SeenFilter', cls_seen_filter.SeenFilter)


class BaseCrawlController:
    def __init__(self, manager, conf, log_file):
        self.manager = manager
        self.conf = conf
        self.stage = 'unified'  # Fixed on unified
        self.logger = LoggerFactory.create_logger(self.conf, "ispider.log", stdout_flag=True)
        self.dom_tld_finished = []
        
        # Locks
        self.shared_lock = self.manager.Lock()
        self.shared_lock_driver = self.manager.Lock()
        self.shared_lock_seen_filter = self.manager.Lock()

        self.seen_filter_manager = self._get_manager_seen_filter()
        self.seen_filter = self.seen_filter_manager.SeenFilter(conf, self.shared_lock_seen_filter)

        self.enqueue_thread = None
        self.shared_new_domains = self.manager.list()
        
        # Stats
        self.shared_script_controller = self.manager.dict({'speedb': [], 'speedu': [], 'running_state': 1, 'bytes': 0, 'tot_counter': 0, 'landings': 0, 'robots': 0, 'sitemaps': 0, 'internal_urls': 0 })

        # Informations by domain
        self.shared_qstats = self.manager.Queue()
        self.shared_dom_stats = cls_domain_stats.SharedDomainStats(
            manager, self.logger, self.shared_lock, self.shared_qstats)
        
        self.lifo_manager = self._get_manager()
        self.queue_out_handler = None

        self.shared_qin = self.manager.Queue(maxsize=conf['QUEUE_MAX_SIZE'])
        self.shared_qout = self.manager.Queue()
        # self.shared_qout = self.lifo_manager.LifoQueue()

        # self.shared_qout = mp.Queue()
        

        self.resume_state = state_manager.ResumeState(self.conf, self)
        self.save_state = state_manager.SaveState(self.conf, self)

        self.processes = []

    def enqueue_new_domains(self, queue_out_handler):
        try:
            while self.shared_script_controller['running_state']:
                try:
                    if self.shared_new_domains:
                        new_domains = list(self.shared_new_domains)
                        while self.shared_new_domains:
                            self.shared_new_domains.pop(0)
                        self.logger.info(f"Adding {len(new_domains)} new domain(s) dynamically.")
                        queue_out_handler.conf['domains'] = new_domains
                        queue_out_handler.fullfill(self.stage)
                except (EOFError, KeyError, BrokenPipeError) as e:
                    self.logger.error(f"Shared proxy no longer available, exiting enqueue_new_domains thread: {e}")
                    self.shared_script_controller['running_state'] = 0
                    break
                except Exception as e:
                    self.logger.error(e)
                time.sleep(3)
            self.logger.info("Closing enqueue_new_domains")
        except KeyboardInterrupt:
            self.logger.warning("Keyboard Interrupt received. Closing the enqueue manager")
            
    def flush_stats_loop(self):
        try:
            while self.shared_script_controller['running_state']:

                try:
                    self.shared_dom_stats.flush_qstats()
                except EOFError:
                    self.logger.warning(f"flush_stats_loop closed by EOF")
                    self.shared_script_controller['running_state'] = 0
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to flush stats: {e}")
                time.sleep(1)  # Flush every 1 second, adjust as needed
            self.logger.info("Closing flush_stats_loop")
        except KeyboardInterrupt:
            logger.warning("Keyboard Interrupt received. Closing the flush stats manager")


    def _get_manager_seen_filter(self):
        m = SeenFilterManager()
        m.start()
        return m

    def _get_manager(self):
        m = MyManager()
        m.start()
        return m

    def _activate_seleniumbase(self):
        if 'seleniumbase' in self.conf['ENGINES']:
            from ispider_core.engines import mod_seleniumbase
            self.logger.info(f"Activating seleniumbase because conf.ENGINES = {self.conf['ENGINES']}")
            mod_seleniumbase.prepare_chromedriver_once()


    def _start_threads(self):
        self.logger.debug("Starting queue input thread...")
        self.processes.append(mp.Process(
            target=thread_queue_in.queue_in_srv, 
            args=(
                self.shared_script_controller, 
                self.shared_dom_stats, 
                self.seen_filter, 
                self.conf,
                self.shared_qin, 
                self.shared_qout, 
            )))

        self.logger.debug("Starting stats thread...")
        self.processes.append(mp.Process(
            target=thread_stats.stats_srv, 
            args=(
                self.shared_script_controller, 
                self.shared_dom_stats, 
                self.seen_filter,
                self.conf,
                self.shared_qin, 
                self.shared_qout, 
            )))

        for proc in self.processes:
            proc.daemon = True
            proc.start()


        # Now start a lightweight thread for dynamic domains
        self.logger.debug("Starting dynamic domain enqueue thread (threading)...")
        self.enqueue_thread = threading.Thread(
            target=self.enqueue_new_domains,
            args=(self.queue_out_handler,),
            daemon=True
        )
        self.enqueue_thread.start()

        # Start stats flushing thread
        self.logger.debug("Starting stats flushing thread (threading)...")
        self.flush_thread = threading.Thread(
            target=self.flush_stats_loop,
            daemon=True
        )
        self.flush_thread.start()

    def _start_crawlers(self, exclusion_list, crawl_func):
        self.logger.debug("Initializing crawler pools...")
        procs = list(range(0, self.conf['POOLS']))
        with mp.Pool(self.conf['POOLS']) as pool:
            pool.starmap(
                crawl_func,
                zip(
                    procs,
                    repeat(self.conf),
                    repeat(exclusion_list),
                    repeat(self.seen_filter),
                    repeat(self.shared_lock),
                    repeat(self.shared_lock_driver),
                    repeat(self.shared_script_controller),
                    repeat(self.shared_dom_stats),
                    repeat(self.shared_qin),
                    repeat(self.shared_qout)
                ))

    def run(self, crawl_func):
        self.logger.info("### BEGINNING CRAWLER")

        try:
            exclusion_list = efiles.load_domains_exclusion_list(self.conf, protocol=False)
            self.logger.info(f"Excluded domains total: {len(exclusion_list)}")

            if self.conf['RESUME']:
                self.logger.info("Loading from resume..")
                self.resume_state.resume_all()
                self.logger.info(f"Tot already Finished: {len(self.dom_tld_finished)}")
           
            self.queue_out_handler = cls_queue_out.QueueOut(
                self.conf, 
                self.shared_dom_stats, 
                self.dom_tld_finished, 
                exclusion_list, 
                self.logger,
                self.shared_qout
            )

            self.queue_out_handler.fullfill(self.stage)
    
            # Activate seleniumbase if in crawlers options            
            self._activate_seleniumbase()

            self.logger.info("Starting threads")
            self._start_threads()

            self.logger.info("Starting crawlers")
            self._start_crawlers(exclusion_list, crawl_func)

        except KeyboardInterrupt:
            self.logger.warning("KeyboardInterrupt received. Shutting down...")

        except Exception as e:
            self.logger.error(e)

        finally:
            unfinished = self.shared_dom_stats.get_unfinished_domains()
            # self.logger.info(f"Unfinished: {unfinished}")
            self.logger.info(f"*** Done {self.shared_script_controller['tot_counter']} PAGES")
            # self._shutdown()
        
        return True

    def _shutdown(self):
        self.logger.info("Shutting down…")
        
        # signal child processes to stop
        self.shared_script_controller["running_state"] = 0

        # join child processes
        for proc in self.processes:
            proc.join()

        # now join the enqueue thread
        if self.enqueue_thread is not None:
            self.enqueue_thread.join()

        # join flush thread (missing)
        if self.flush_thread is not None:
            self.flush_thread.join()

        # Save state
        self.logger.info("Saving state..") 
        self.save_state.save_all()

        # self.save_queues()
        self.logger.info("Queue states saved")

        self.logger.info("All threads and processes stopped.")


class CrawlController(BaseCrawlController):
    def __init__(self, manager, conf):
        super().__init__(
            manager, conf, "stage_crawl_ctrl.log")

    def run(self):
        return super().run(stage_crawl.crawl)

class SpiderController(BaseCrawlController):
    def __init__(self, manager, conf):
        super().__init__(
            manager, conf, "stage_spider_ctrl.log")

    def run(self):
        return super().run(stage_spider.spider)


class UnifiedController(BaseCrawlController):
    def __init__(self, manager, conf):
        super().__init__(
            manager, conf, "stage_unified_ctrl.log")

    def run(self):
        from ispider_core.crawlers import stage_unified
        return super().run(stage_unified.unified)

