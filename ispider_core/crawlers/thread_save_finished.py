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
            fnt = Path(conf['path_data']) / f"{conf['method']}_dom_stats_finished.pkl.tmp"
            fn = Path(conf['path_data']) / f"{conf['method']}_dom_stats_finished.pkl"

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
            time.sleep(120)

            # Running State Check
            if script_controller['running_state'] == 1:
                logger.debug("** SAVE FINISHED - NOT READY YET")
                continue

            last_saved_delay = time.time() - t0
            if last_saved_delay < 180 and script_controller['running_state'] != 0:
                continue  # Wait longer before saving

            logger.info(f"Saving the finished state after {round(last_saved_delay)} seconds")
            save_pickle_file()

            if script_controller['running_state'] == 0:
                logger.info("closing saved_finished")
                break

    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt received. Skipping save operation.")

    return True
