from ispider_core.orchestrator import Orchestrator
import multiprocessing
import os
from pathlib import Path

from ispider_core import settings

class ISpider:
    def __init__(self, domains, stage=None, **kwargs):
        """
        Initialize the ISpider class.
        :param domains: List of domains to crawl.
        :param stage: Optional - Run a specific stage (e.g., 'stage1').
        :param kwargs: Additional configuration options.
        """
        self.stage = stage  # Save the selected stage
        self.conf = self._setup_conf(domains, kwargs)
        self.manager = multiprocessing.Manager()
        self.shared_counter = self.manager.Value('i', 0)
        self._ensure_user_folder()

    def _setup_conf(self, domains, kwargs):
        """
        Prepare the configuration dictionary.
        """
        conf = {
            'method': 'stage1',  # Default first step
            'domains': domains,
            'dumps': 'dump',
            **kwargs  # Allow overriding with custom params
        }
        return conf

    def _ensure_user_folder(self):
        """
        Check if ~/.ispider exists. If not, ask the user for permission to create it.
        """
        user_folder = Path.home() / ".ispider"
        data_folder = user_folder / "data"
        sources_folder = user_folder / "sources"

        if not user_folder.exists():
            response = input(f"""The directory {user_folder} is required. \nAll the data will be saved there. Do you want to create it? [y/N]: """).strip().lower()
            if response != 'y':
                print("Aborting setup. The program cannot continue without this folder.")
                exit(1)  # Stop execution if user denies permission

            try:
                data_folder.mkdir(parents=True, exist_ok=True)
                sources_folder.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {data_folder} and {sources_folder}")
            except PermissionError:
                print(f"❌ Error: No permission to create {user_folder}.")
                exit(1)

    def run(self):
        """
        Execute the selected stage or all 4 stages.
        """
        if self.stage:
            # Run only the specified stage
            self.conf['method'] = self.stage
            Orchestrator(self.conf, self.manager, self.shared_counter).run()
        else:
            # Run all 4 steps sequentially
            for step in ['stage1', 'stage2', 'stage3', 'stage4']:
                self.conf['method'] = step
                Orchestrator(self.conf, self.manager, self.shared_counter).run()

        return self._fetch_results()

    def _fetch_results(self):
        """
        Retrieve results from the dump folder or database.
        """
        return {}
