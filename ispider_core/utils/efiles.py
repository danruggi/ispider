import csv
import validators
import importlib.resources

from ispider_core import utils
from pathlib import Path

def load_domains_exclusion_list(conf, protocol=True):
    """
    Load the domain exclusion list from a CSV file.

    :param conf: Dictionary containing configuration, including 'PATH_SOURCES'.
    :param protocol: Whether to add HTTPS protocol to domains.
    :return: List of valid domains.
    :raises FileNotFoundError: If the CSV file is not found.
    :raises ValueError: If there are issues with the data format.
    """
    out = []

    try:
        # Use pathlib to ensure compatibility
        file_path = Path.home() / ".ispider" / "data" / "exclude_domains.csv"

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
                    domain = utils.add_https_protocol(domain)

                out.append(domain)

        return out

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Domain exclusion list file not found: {file_path}") from e

    except Exception as e:
        raise ValueError(f"Error processing domain exclusion list: {str(e)}") from e
