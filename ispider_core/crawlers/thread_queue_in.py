import time
import random
import multiprocessing as mp
from queue import Empty  # Import to catch queue exceptions

from ispider_core.utils import queues
from ispider_core.utils import ifiles
from ispider_core.utils import controllers

from ispider_core.utils.logger import LoggerFactory

def queue_in_srv(
    script_controller, fetch_controller, lock, 
    seen_filter, conf, qin, qout):
    
    logger = LoggerFactory.create_logger("./logs", "queue_in.log", log_level=conf['LOG_LEVEL'], stdout_flag=True)
    
    Q_MAX = conf['QUEUE_MAX_SIZE']
    Q_BLOCK_MAX = max(min(Q_MAX, 5000), Q_MAX // 2)
    Q_BLOCK_MIN = max(min(Q_MAX, 1000), Q_MAX // 10)

    to_insert = []

    logger.info("Begin Queue Process")
    
    t0 = time.time()

    try:
        while True:
            # Queue management every ~5 seconds
            if time.time() - t0 > 5:
                if script_controller['running_state'] == 0:
                    logger.info("State Controller 0: Finishing Thread Q_IN")
                    # logger.info(f"TOT INSERTED (DURLS): {len(durls)}")
                    break
                t0 = time.time()

            reqA = None
            if not qout.empty():
                try:
                    reqA = qout.get(timeout=1)
                    #--------------------
                    # Verify if in seen
                    if seen_filter.req_in_seen(reqA):
                        controllers.reduce_fetch_controller(fetch_controller, lock, reqA[2])
                        continue
                    #--------------------
                except Empty:
                    pass

            if reqA is not None:
                to_insert.append(reqA)

            if len(to_insert) < Q_BLOCK_MIN and qout.qsize() == 0 and not qin.empty():
                # logger.debug(f"Qwait case 1 --> {len(to_insert)} -- {Q_BLOCK_MIN} -- {qout.qsize()} -- {qin.empty()}")
                time.sleep(2)  # Lower sleep time for responsiveness

            if len(to_insert) >= Q_BLOCK_MAX or qout.qsize() == 0:
                while qin.qsize() >= Q_MAX // 2:
                    time.sleep(2)

                # Ensure function exists before calling
                to_insert = queues.sparse_q_elements(to_insert)

                for el in to_insert:
                    seen_filter.add_to_seen_req(el)
                    qin.put(el)

                to_insert.clear()

    except KeyboardInterrupt:
        logger.warning(f"Missing to insert: {len(to_insert)}")
        logger.warning("Closing the q_in queue manager")
