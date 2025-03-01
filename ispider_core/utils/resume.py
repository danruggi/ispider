import os
import json
import re
import pickle
import shutil
from pathlib import Path

from ispider_core import settings
from ispider_core.utils.logger import LoggerFactory

logger = LoggerFactory.create_logger(
    "./logs", "crawlResumeState.log",
    log_level='DEBUG',
    stdout_flag=True
)

class CrawlResumeState:
    def __init__(self, conf):
        """
        Handles loading and cleaning up domain crawl states.

        :param conf: Configuration dictionary with required paths.
        """
        self.conf = conf
        self.dom_tld_finished = self.load_finished_domains()

    def load_finished_domains(self):
        """Loads the finished domains from a pickle file."""
        dom_tld_finished = set()
        pickle_file = Path(self.settings.PATH_DATA) / 'crawl_shared_fetch_controller.pkl'

        try:
            logger.debug(f"Loading finished domains from {pickle_file}")
            if pickle_file.exists():
                with open(pickle_file, 'rb') as f:
                    dom_tld_finished = pickle.load(f)
                logger.info(f"Loaded {len(dom_tld_finished)} finished domains.")
            else:
                logger.warning(f"Pickle file not found: {pickle_file}")

        except Exception as e:
            logger.error(f"Error loading finished domains: {e}")

        return dom_tld_finished

    def remove_unfinished_domains(self):
        """Removes unfinished domains from JSON files and deletes their dump directories."""
        tot_lines_removed = 0
        path_data = Path(self.settings.PATH_DATA)
        path_dumps = Path(self.conf['PATH_DUMPS'])

        for file in path_data.iterdir():
            if not re.match(r'crawl_conn_meta.*\.json', file.name):
                continue

            with file.open() as f:
                filtered_lines = []
                lines_removed = 0

                for line in f:
                    data = json.loads(line)
                    dom_tld = data.get('dom_tld')

                    if dom_tld not in self.dom_tld_finished:
                        lines_removed += 1
                        dump_path = path_dumps / dom_tld
                        if dump_path.exists() and dump_path.is_dir():
                            shutil.rmtree(dump_path)
                        continue  # Skip this line

                    filtered_lines.append(line)

            tot_lines_removed += lines_removed
            logger.info(f"{file.name}: Removed {lines_removed} lines. Total removed: {tot_lines_removed}")

            if not filtered_lines:
                logger.warning(f"No valid lines left in {file.name}. Deleting file.")
                file.unlink()
                continue

            if lines_removed > 0:
                tmp_file = file.with_suffix(".tmp")
                with tmp_file.open("w") as f:
                    f.writelines(filtered_lines)
                tmp_file.replace(file)

        logger.info(f"Total lines removed: {tot_lines_removed}")
        logger.info(f"Total finished domains: {len(self.dom_tld_finished)}")
        return tot_lines_removed
