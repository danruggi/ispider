import multiprocessing
import os
import requests
from pathlib import Path

from ispider_core.utils.logger import LoggerFactory
from ispider_core.orchestrator import Orchestrator

from ispider_core import config

class ISpider:
    def __init__(self, domains, stage=None, **kwargs):
        """
        Initialize the ISpider class.
        :param domains: List of domains to crawl.
        :param stage: Optional - Run a specific stage (e.g., 'landings').
        :param kwargs: Additional configuration options.
        """
        self.stage = stage
        self.manager = None
        self.shared_counter = None
        self.conf = self._setup_conf(domains, kwargs)
        self.logger = LoggerFactory.create_logger("./logs", "ispider.log", log_level=self.conf['LOG_LEVEL'], stdout_flag=True)
        
        self._prepare_directories()
        self._download_csv_if_needed()
        
        # self.logger.debug(f"Logger handlers count: {len(self.logger.handlers)}")


    def _setup_conf(self, domains, kwargs):
        settings = config.Settings()
        conf = settings.to_dict()
        conf.update({
            'domains': domains,
            'method': self.stage or 'landings',
            **kwargs  # user passed settings
        })

        base = Path(os.path.expanduser(conf['USER_FOLDER']))
        conf.update({
            'path_data': base / 'data',
            'path_dumps': base / 'data' / 'dumps',
            'path_jsons': base / 'data' / 'jsons'
        })
        return conf

    def _get_user_folder(self):
        """Ensure the USER_FOLDER from settings exists and return it as a Path."""
        raw_path = self.conf['USER_FOLDER']
        user_folder = Path(os.path.expanduser(raw_path)).resolve()

        if not user_folder.parent.exists():
            raise Exception(f"Parent folder {user_folder.parent} does not exist")

        user_folder.mkdir(parents=True, exist_ok=True)
        return user_folder
        
    def _prepare_directories(self):
        for subfolder in ['data', 'data/dumps', 'data/jsons', 'sources']:
            (self._get_user_folder() / subfolder).mkdir(parents=True, exist_ok=True)

    def _download_csv_if_needed(self):
        csv_url = "https://raw.githubusercontent.com/danruggi/ispider/refs/heads/main/static/exclude_domains.csv"
        csv_path = self._get_user_folder() / "sources" / "exclude_domains.csv"
        if not csv_path.exists():
            try:
                response = requests.get(csv_url, timeout=10)
                response.raise_for_status()
                csv_path.write_bytes(response.content)
                self.logger.info(f"Downloaded {csv_path}")
            except requests.RequestException as e:
                self.logger.error(f"Failed to download CSV: {e}")

    def _ensure_manager(self):
        if self.manager is None:
            self.manager = multiprocessing.Manager()
            self.shared_counter = self.manager.Value('i', 0)


    def run(self):
        """ Run the specified stage or all sequentially """
        self._ensure_manager()
        orchestrator = Orchestrator(self.conf, self.manager, self.shared_counter)
        if self.stage:
            self.logger.info(f"*** Running Stage: {self.stage}")
            self.conf['method'] = self.stage
            orchestrator.run()
        else:
            self.logger.info("*** Running All Stages")
            for stage in ['crawl', 'spider']:
                self.conf['method'] = stage
                orchestrator.run()
        return self._fetch_results()

    def _fetch_results(self):
        return {}
