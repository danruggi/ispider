import multiprocessing
import os
import requests
from pathlib import Path

from ispider_core.utils.logger import LoggerFactory
from ispider_core.orchestrator import Orchestrator

from ispider_core import config

from importlib.metadata import version, PackageNotFoundError

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
        self.orchestrator = None

        self.conf = self._setup_conf(domains, kwargs)
        
        self.logger = LoggerFactory.create_logger(self.conf, "ispider.log", stdout_flag=True)
        self._prepare_directories()
        self._download_csv_if_needed()
        
        # self.logger.debug(f"Logger handlers count: {len(self.logger.handlers)}")

    @property
    def shared_new_domains(self):
        self.logger.info("Ispider, Adding Domains..")
        if self.orchestrator:
            return getattr(self.orchestrator, 'shared_new_domains', None)
        self.logger.info("No attribute shared_new_domains")
        return None

    @property
    def shared_dom_stats(self):
        if self.orchestrator:
            return getattr(self.orchestrator, 'shared_dom_stats', None)
        return None

    @property
    def shared_script_controller(self):
        if self.orchestrator:
            return getattr(self.orchestrator, 'shared_script_controller', None)
        return None

    def _setup_conf(self, domains, kwargs):
        settings = config.Settings()
        conf = settings.to_dict()

        upper_kwargs = {k.upper(): v for k, v in kwargs.items()}

        conf.update({
            'domains': domains,
            'method': self.stage or 'landings',
            **upper_kwargs  # user passed settings
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


    def run(self):
        """ Run the specified stage or all sequentially """
        self._ensure_manager()
        self.orchestrator = Orchestrator(self.conf, self.manager)

        try:
            self.logger.info(f"Package version: {version('ispider')}")
        except PackageNotFoundError:
            self.logger.info("Package not installed or name mismatch.")

        self.logger.info(f"Using output folder: {self._get_user_folder()}")
        
        if self.stage:
            self.logger.info(f"*** Running Stage: {self.stage}")
            self.conf['method'] = self.stage
            self.orchestrator.run()

        else:
            self.logger.info("*** Running Unified as default")    
            self.conf['method'] = 'unified'
            self.orchestrator.run()

        return self._fetch_results()

    def _fetch_results(self):
        return {}

    def shutdown(self):
        if self.orchestrator:
            # Tell orchestrator and controller to stop threads and processes
            self.orchestrator.shutdown()

        # Only after all threads/processes joined, then shutdown manager
        if self.manager:
            self.manager.shutdown()

        self.logger.info("Ispider shutdown complete")
