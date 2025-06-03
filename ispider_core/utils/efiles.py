import csv
import validators
import importlib.resources

from ispider_core.utils import domains
from pathlib import Path

def load_domains_exclusion_list(conf, protocol=True):
    out = []
    try:
        file_path = Path.home() / ".ispider" / "sources" / "exclude_domains.csv"
        with file_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=',', quotechar='"')
            valid_keys = ['domain', 'dom_tld']
            column_key = next((key for key in valid_keys if key in reader.fieldnames), None)
            if not column_key:
                raise ValueError(f"Missing required column. Expected one of: {valid_keys}")
            for row in reader:
                domain = row.get(column_key, "").strip()
                if not domain or not validators.domain(domain):
                    continue  # Skip invalid domains
                if protocol:
                    domain = domains.add_https_protocol(domain)
                out.append(domain)
    except:
        pass
    return out