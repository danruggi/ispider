from ispider_core import settings
from ispider_core.utils.logger import LoggerFactory
from ispider_core.utils import efiles


from queue import LifoQueue

import multiprocessing as mp

logger = LoggerFactory.create_logger(
            "./logs", "stage_1.log",
            log_level='DEBUG',
            stdout_flag=True
        )


def get_manager():

    # create manager that knows how to create and manage LifoQueues
    class MyManager(mp.managers.BaseManager):
        pass

    MyManager.register('LifoQueue', LifoQueue)
    m = MyManager()
    m.start()
    return m

def _stage1_crawl_bot(manager, shared_counter, conf):
    logger.info("### BEGINNING CRAWLER LAND_ROB_SM");

    print(settings)
    print(conf)

    procs = list(range(0,settings.POOLS))
    shared_script_controller = manager.dict({'speedb': list(), 'speedu': list(), 'running_state': 1, 'landings': 0, 'robots': 0, 'sitemaps': 0, 'bytes': 0})
    shared_fetch_controller = manager.dict()
    shared_lock = manager.Lock()
    shared_qin = manager.Queue(maxsize=settings.QUEUE_MAX_SIZE)

    m = get_manager()
    shared_qout = m.LifoQueue()

    # Get domain exclusion list
    exclusion_list = efiles.load_domains_exclusion_list(conf, protocol=False)
    logger.info(f"Excluded domains total: {len(exclusion_list)}")

    dom_tld_finished = set(crawl_load_dom_tld_finished(conf))
    logger.info("Tot already Finished:", len(dom_tld_finished), 7)

    tot_removed_unfinished = crawl_remove_unfinished_dom_tld_from_jsons(dom_tld_finished, conf)
    ppprint("Removed", tot_removed_unfinished ,"files of unfinished dom_tld from crawl meta jsons")

    ppprint("Fullfill the queue")
    crawl_queue_fullfill(conf, _all_urls, shared_fetch_controller, dom_tld_finished, exclusion_list, shared_qout)

    tq0 = mp.Process(
        target=queue_in,
        args=(
                shared_script_controller,
                shared_fetch_controller,
                shared_lock,
                shared_qin,
                shared_qout,
                conf
        )
    )
    tq0.start()


    ppprint("Init Stats Thread")
    t1 = mp.Process(
        target=statsCalc,
            args=(
                shared_counter,
                shared_script_controller,
                shared_fetch_controller,
                shared_qout,
                shared_qin,
                conf
            )
        )
    t1.daemon = True
    t1.start()

    # Will Save the fetch_controller
    ppprint("Init Save All Finished Thread")
    t2 = mp.Process(
        target = save_finished,
            args=(
                shared_script_controller,
                shared_fetch_controller,
                shared_lock,
                conf
            )
        )
    # t2.daemon = True
    t2.start()

    ppprint("Init Crawler Pools")
    try:
        with mp.Pool(conf['POOLS']) as p:
            out = p.starmap(crawl,
                zip(
                    procs,
                    repeat(conf),
                    repeat(exclusion_list),
                    repeat(shared_counter),
                    repeat(shared_lock),
                    repeat(shared_script_controller),
                    repeat(shared_fetch_controller),
                    repeat(shared_qin),
                    repeat(shared_qout)
                )
            )
    except KeyboardInterrupt:
        ppprint("Setting the finished flag to close pending threads")
        shared_script_controller['running_state'] = 0;
        t1.join()
        t2.join()
        tq0.join()
        return

    except Exception as e:
        ppprint(e, 2)

    unfinished = [x for x,v in shared_fetch_controller.items() if shared_fetch_controller[x] > 0]
    ppprint("Unfinished:",unfinished, 5)

    ppprint("Setting the finished flag to close pending threads")
    shared_script_controller['running_state'] = 0;
    t1.join()
    t2.join()
    tq0.join()

    try:
        ppprint("*** Done", shared_counter.value, "PAGES", 5)
    except Exception as e:
        ppprint(e, 0)

    return True
