""" crawlers/thread_save_finished.py """

import os
import time
import pickle
from pathlib import Path
from datetime import datetime

from ispider_core.utils.logger import LoggerFactory

def save_finished(script_controller, dom_stats, lock, conf):
    logger = LoggerFactory.create_logger(conf, "ispider.log", stdout_flag=True)

    def save_pickle_file(withLock=True):
        t0 = time.time()
        finished_domains = dom_stats.get_finished_domains()

        logger.debug(f"Pickle td got from dom_stats in {time.time() - t0:.2f} seconds")
        logger.debug(f"Pickle set: {len(finished_domains)} as finished")

        if finished_domains:
            fnt = Path(conf['path_data']) / f"dom_stats_finished.pkl.tmp"
            fn = Path(conf['path_data']) / f"dom_stats_finished.pkl"

            # Save to temporary file
            t0 = time.time()
            with open(fnt, 'wb') as f:
                pickle.dump(finished_domains, f)
            logger.debug(f"Pickle saved in {time.time() - t0:.2f} seconds in tmp file")

            # Rename it atomically
            t0 = time.time()
            os.replace(fnt, fn)
            logger.debug(f"Pickle renamed in {time.time() - t0:.2f} seconds in dst file")

        return True

    logger.debug("Begin saved Finished Process")
    t0 = time.time()

    try:
        while True:

            if not script_controller['running_state']:
                logger.info("Closing saved_finished")
                break

            # Running State Check
            if script_controller['running_state'] == 1:
                logger.debug("** SAVE FINISHED - NOT READY YET")
                time.sleep(5)
                continue

            else:

                tdiff = time.time() - t0
                if tdiff <= 180:
                    time.sleep(5)
                    continue
                t0 = time.time()

                logger.info(f"Saving the finished state after {round(tdiff)} seconds")
                save_pickle_file()

            time.sleep(5)

    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt received. Skipping save operation.")

    return True
