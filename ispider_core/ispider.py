from ispider_core.orchestrator import Orchestrator
import multiprocessing
import os
import requests
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
        self.user_folder, self.sources_folder = self._ensure_user_folder()
        self._download_csv_if_needed()

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
        Ensure ~/.ispider exists. If not, ask for permission to create it.
        """
        user_folder = Path.home() / ".ispider"
        data_folder = user_folder / "data"
        sources_folder = user_folder / "sources"

        if not user_folder.exists():
            response = input(f"""The directory {user_folder} is required. \nAll data will be saved there. Do you want to create it? [y/N]: """).strip().lower()
            if response != 'y':
                print("Aborting setup. The program cannot continue without this folder.")
                exit(1)

            try:
                data_folder.mkdir(parents=True, exist_ok=True)
                sources_folder.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {data_folder} and {sources_folder}")
            except PermissionError:
                print(f"❌ Error: No permission to create {user_folder}.")
                exit(1)

        return user_folder, sources_folder

    def _download_csv_if_needed(self):
        """
        Check if the CSV file exists, if not, download it.
        """
        csv_url = "https://raw.githubusercontent.com/danruggi/ispider/dev/static/exclude_domains.csv"
        csv_path = self.sources_folder / "exclude_domains.csv"

        if not csv_path.exists():
            print(f"🔍 CSV file not found. Downloading from {csv_url}...")
            try:
                response = requests.get(csv_url, timeout=10)
                response.raise_for_status()  # Raise an error for HTTP issues

                with open(csv_path, "wb") as f:
                    f.write(response.content)

                print(f"✅ Exclusion domains CSV file saved to {csv_path}")
            except requests.RequestException as e:
                print(f"❌ Failed to download Exclusion domains CSV: {e}")

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
