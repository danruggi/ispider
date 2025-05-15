import multiprocessing
import os
import requests
from pathlib import Path

from ispider_core import settings
from ispider_core.utils.logger import LoggerFactory
from ispider_core.orchestrator import Orchestrator

class ISpider:
    def __init__(self, domains, stage=None, **kwargs):
        """
        Initialize the ISpider class.
        :param domains: List of domains to crawl.
        :param stage: Optional - Run a specific stage (e.g., 'stage1').
        :param kwargs: Additional configuration options.
        """
        self.stage = stage
        self.manager = multiprocessing.Manager()
        self.shared_counter = self.manager.Value('i', 0)
        self.conf = self._setup_conf(domains, kwargs)
        self.logger = LoggerFactory.create_logger("./logs", "ispider.log", log_level='DEBUG', stdout_flag=True)
        self._prepare_directories()
        self._download_csv_if_needed()

    def _setup_conf(self, domains, kwargs):
        return {
            'method': 'stage1',  # Default step
            'domains': domains,
            'path_dumps': self._get_user_folder() / 'data' / 'dumps',
            'path_jsons': self._get_user_folder() / 'data' / 'jsons',
            'path_data': self._get_user_folder() / 'data',
            **kwargs
        }

    def _get_user_folder(self):
        """ Ensure ~/.ispider exists """
        default_folder = Path.home() / ".ispider"
        user_folder = Path(os.getenv("ISPIDER_FOLDER", default_folder))
        if not user_folder.parent.exists():
            raise Exception(f"Folder {user_folder.parent} not exists")
        user_folder.mkdir(parents=True, exist_ok=True)
        return user_folder

    def _prepare_directories(self):
        for subfolder in ['data', 'data/dumps', 'data/jsons', 'sources']:
            (self._get_user_folder() / subfolder).mkdir(parents=True, exist_ok=True)

    def _download_csv_if_needed(self):
        csv_url = "https://raw.githubusercontent.com/danruggi/ispider/dev/static/exclude_domains.csv"
        csv_path = self._get_user_folder() / "sources" / "exclude_domains.csv"
        if not csv_path.exists():
            try:
                response = requests.get(csv_url, timeout=10)
                response.raise_for_status()
                csv_path.write_bytes(response.content)
                self.logger.info(f"Downloaded {csv_path}")
            except requests.RequestException as e:
                self.logger.error(f"Failed to download CSV: {e}")

    def run(self):
        """ Run the specified stage or all sequentially """
        orchestrator = Orchestrator(self.conf, self.manager, self.shared_counter)
        if self.stage:
            self.logger.info(f"*** Running Stage: {self.stage}")
            self.conf['method'] = self.stage
            orchestrator.run()
        else:
            self.logger.info("*** Running All Stages")
            for stage in ['stage1', 'stage2']:
                self.conf['method'] = stage
                orchestrator.run()
        return self._fetch_results()

    def _fetch_results(self):
        return {}
