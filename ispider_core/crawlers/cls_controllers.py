from ispider_core.utils.logger import LoggerFactory
from ispider_core.utils import efiles
from ispider_core.utils import resume

from ispider_core.crawlers import cls_queue_out
from ispider_core.crawlers import cls_seen_filter
from ispider_core.crawlers import thread_queue_in
from ispider_core.crawlers import thread_stats
from ispider_core.crawlers import thread_save_finished
from ispider_core.crawlers import stage_crawl, stage_spider

from queue import LifoQueue
import multiprocessing as mp
import time
from itertools import repeat

from multiprocessing.managers import BaseManager

class MyManager(BaseManager):
    pass

class SeenFilterManager(BaseManager):
    pass
    
MyManager.register('LifoQueue', LifoQueue)
SeenFilterManager.register('SeenFilter', cls_seen_filter.SeenFilter)

class BaseCrawlController:
    def __init__(self, manager, conf, shared_counter, log_file):
        self.manager = manager
        self.conf = conf
        self.shared_counter = shared_counter
        self.stage = conf['method']  # Reflect the stage
        self.logger = LoggerFactory.create_logger("./logs", log_file, log_level=conf['LOG_LEVEL'], stdout_flag=True)
        
        self.lifo_manager = self._get_manager()

        self.shared_lock = self.manager.Lock()
        self.shared_lock_driver = self.manager.Lock()
        self.shared_lock_seen_filter = self.manager.Lock()

        self.seen_filter_manager = self._get_manager_seen_filter()
        self.seen_filter = self.seen_filter_manager.SeenFilter(conf, self.shared_lock_seen_filter)

        self.shared_script_controller = self.manager.dict({'speedb': [], 'speedu': [], 'running_state': 1, 'bytes': 0})  # Stats
        self.shared_fetch_controller = self.manager.dict()          # Increase and decrease page count por domain
        self.shared_totpages_controller = self.manager.dict()      # Increase page count por domain
        self.shared_qin = self.manager.Queue(maxsize=conf['QUEUE_MAX_SIZE'])
        self.shared_qout = self.lifo_manager.LifoQueue()
        self.processes = []

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
            mod_seleniumbase.prepare_chromedriver_once()

    def run(self, crawl_func):
        self.logger.info("### BEGINNING CRAWLER")

        exclusion_list = efiles.load_domains_exclusion_list(self.conf, protocol=False)
        self.logger.info(f"Excluded domains total: {len(exclusion_list)}")

        dom_tld_finished = resume.ResumeState(self.conf, self.stage).load_finished_domains()
        self.logger.info(f"Tot already Finished: {len(dom_tld_finished)}")

        queue_out_handler = cls_queue_out.QueueOut(
            self.conf, 
            self.shared_fetch_controller, 
            self.shared_totpages_controller, 
            dom_tld_finished, 
            exclusion_list, 
            self.shared_qout)
        queue_out_handler.fullfill(self.stage)
        
        self.logger.info(f"Loaded {self.seen_filter.bloom_len()} in seen_filter")

        self._activate_seleniumbase()
        self._start_threads()
        self._start_crawlers(exclusion_list, crawl_func)

        unfinished = [x for x, v in self.shared_fetch_controller.items() if v > 0]
        self.logger.info(f"Unfinished: {unfinished}")

        self._shutdown()
        self.logger.info(f"*** Done {self.shared_counter.value} PAGES")
        return True

    def _start_threads(self):
        self.logger.info("Starting queue input thread...")
        self.processes.append(mp.Process(
            target=thread_queue_in.queue_in_srv, 
            args=(
                self.shared_script_controller, 
                self.shared_fetch_controller, 
                self.shared_lock, 
                self.seen_filter, 
                self.conf,
                self.shared_qin, 
                self.shared_qout, 
            )))

        self.logger.info("Starting stats thread...")
        self.processes.append(mp.Process(
            target=thread_stats.stats_srv, 
            args=(
                self.shared_counter, 
                self.shared_script_controller, 
                self.shared_fetch_controller, 
                self.seen_filter,
                self.conf,
                self.shared_qout, 
                self.shared_qin, 
            )))

        self.logger.info("Starting save finished thread...")
        self.processes.append(mp.Process(
            target=thread_save_finished.save_finished, 
            args=(
                self.shared_script_controller, 
                self.shared_fetch_controller, 
                self.shared_lock, 
                self.conf
            )))

        for proc in self.processes:
            proc.daemon = True
            proc.start()

    def _start_crawlers(self, exclusion_list, crawl_func):
        self.logger.info("Initializing crawler pools...")
        procs = list(range(0, self.conf['POOLS']))
        with mp.Pool(self.conf['POOLS']) as pool:
            pool.starmap(
                crawl_func,
                zip(
                    procs,
                    repeat(self.conf),
                    repeat(exclusion_list),
                    repeat(self.seen_filter),
                    repeat(self.shared_counter),
                    repeat(self.shared_lock),
                    repeat(self.shared_lock_driver),
                    repeat(self.shared_script_controller),
                    repeat(self.shared_fetch_controller),
                    repeat(self.shared_totpages_controller),
                    repeat(self.shared_qin),
                    repeat(self.shared_qout)
                ))

    def _shutdown(self):
        self.logger.info("Shutting down...")
        self.shared_script_controller["running_state"] = 0
        for proc in self.processes:
            proc.join()

class CrawlController(BaseCrawlController):
    def __init__(self, manager, conf, shared_counter):
        super().__init__(
            manager, conf, shared_counter, "stage_crawl_ctrl.log")
        self.shared_script_controller.update({'landings': 0, 'robots': 0, 'sitemaps': 0})

    def run(self):
        return super().run(stage_crawl.crawl)

class SpiderController(BaseCrawlController):
    def __init__(self, manager, conf, shared_counter):
        super().__init__(
            manager, conf, shared_counter, "stage_spider_ctrl.log")
        self.shared_script_controller.update({'internal_urls': 0})

    def run(self):
        return super().run(stage_spider.spider)
