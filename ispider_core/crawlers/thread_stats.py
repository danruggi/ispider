import time
import json
import os
import heapq
import pickle

from collections import deque, Counter
from datetime import datetime

from ispider_core.utils.logger import LoggerFactory


def stats_srv(
    shared_script_controller, shared_dom_stats,
    seen_filter, conf,
    shared_qin, shared_qout):
    '''
    shared_script_controller: [Landing, Robots, Sitemaps, Bytes Downloaded]
    '''
    logger = LoggerFactory.create_logger(conf, "ispider.log", stdout_flag=True)

    start = datetime.now()
    logger.debug(f"Start Time: {start}")
    start_datetime = start.strftime("%Y-%m-%d %H:%M")

    x0 = time.time()
    t0 = time.time()
    speeds = deque(maxlen=10)
    req_count = 0

    try:
        while True:
            time.sleep(5)

            tdiff = time.time() - t0
            if tdiff <= 30:
                continue

            t0 = time.time()

            # Running State
            if shared_script_controller['running_state'] == 0:
                logger.info("Closing stats")
                logger.info(f"** STATS FINISHED IN: {round((time.time() - x0), 2)} seconds")
                break
            elif shared_script_controller['running_state'] == 1:
                logger.debug(f"** STATS NOT READY YET - Q SIZE: {shared_qout.qsize()}")
                continue

            # Fulfill speed deque to get averaged speed
            try:
                speeds.append((shared_script_controller['bytes'], t0))
                shared_script_controller['bytes'] = 0
            except Exception as e:
                logger.warning(f"Error updating speeds deque: {e}")

            # Get instant requests per minute
            current_count = shared_script_controller.get('tot_counter', 0)
            req_per_min = round((((current_count - req_count) / tdiff) * 60), 2)
            req_count = current_count

            if len(speeds) < 2:
                continue

            try:
                speed_mb = round(
                    (sum([t[0] for t in list(speeds)[1:]]) / (speeds[-1][1] - speeds[0][1])) / 1024, 2
                )


                count_all_domains = shared_dom_stats.get_tot_domains()
                count_finished_domains = shared_dom_stats.count_by(lambda v: v == 0)
                count_unfinished_domains = count_all_domains - count_finished_domains
                count_bigger_domains = shared_dom_stats.count_by(lambda v: v > 100)
                sorted_dom_missing = shared_dom_stats.get_sorted_missing(reverse=True)
                bl = [f"{k}:{v}" for k, v in list(sorted_dom_missing.items())[:20]]
                sl = [f"{k}:{v}" for k, v in list(sorted_dom_missing.items()) if v > 0][-5:]

                logger.info("******************* STATS ***********************")
                logger.info(f"#### SPEED: {speed_mb} Kb/s")
                logger.info(f"#### REQ PER MIN: {req_per_min} urls")
                logger.info(f"*** [Start at: {start_datetime}]")
                logger.info(f"*** [Requests: {current_count}/{int((t0 - start.timestamp()) / 60)}m] "
                            f"QOUT SIZE: {shared_qout.qsize()} QIN SIZE: {shared_qin.qsize()}")
                logger.info(f"*** [Finished: {count_finished_domains}/{count_all_domains}] - Incomplete: {count_unfinished_domains} "
                            f"- [More than 100: {count_bigger_domains}]")
                logger.info(f"Landings:  {shared_script_controller.get('landings', 0)}")
                logger.info(f"Robots:    {shared_script_controller.get('robots', 0)}")
                logger.info(f"Sitemaps:  {shared_script_controller.get('sitemaps', 0)}")
                logger.info(f"Internals: {shared_script_controller.get('internal_urls', 0)}")
                logger.info(f"T5: {bl}")
                logger.info(f"B5: {sl}")

                logger.info(f"Seen Filter len: {seen_filter.bloom_len()}")

            except Exception as e:
                logger.warning(f"Stats Not available at the moment: {e}")

    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt received - FINISH STATS")
