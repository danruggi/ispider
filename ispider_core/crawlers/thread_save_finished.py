import os
import time
import pickle
from pathlib import Path
from datetime import datetime

from ispider_core.utils.logger import LoggerFactory

def save_finished(script_controller, fetch_controller, lock, conf):
    logger = LoggerFactory.create_logger("./logs", "save_finished.log", log_level=conf['LOG_LEVEL'], stdout_flag=True)

    def save_pickle_file(withLock=True):
        t0 = time.time()
        finished_domains = [k for k, v in fetch_controller.items() if v == 0]

        logger.debug(f"Pickle td got from fetch_controller in {time.time() - t0:.2f} seconds")
        logger.debug(f"Pickle set: {len(finished_domains)} as finished")

        if finished_domains:
            fnt = Path(conf['path_data']) / f"{conf['method']}_shared_fetch_controller.pkl.tmp"
            fn = Path(conf['path_data']) / f"{conf['method']}_shared_fetch_controller.pkl"

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

    logger.info("Begin saved Finished Process")
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
                logger.info("SAVE FINISHED URLS FINISHED")
                break

    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt received. Skipping save operation.")

    return True
