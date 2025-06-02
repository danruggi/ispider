from seleniumbase import SB
from datetime import datetime
from ispider_core.utils import domains
from ispider_core.parsers import filetype_parser

from seleniumbase import Driver

# One-time setup before launching workers
def prepare_chromedriver_once():
    # This triggers the download/setup of uc_driver in a single process
    driver = Driver(uc=True, headless=True)
    driver.quit()

def fetch_with_seleniumbase(reqA, lock_driver, mod, conf=None):
    url, request_discriminator, dom_tld, retries, depth, engine = reqA
    metadata = {
        'url': url,
        'request_discriminator': request_discriminator,
        'dom_tld': dom_tld,
        'retries': retries,
        'depth': depth,
        'mod': mod,
        'engine': engine,
        'status_code': -1,
        'error_message': None,
        'num_bytes_downloaded': 0,
        'connection_time': datetime.utcnow().isoformat(),
        'browser_type': 'seleniumbase',
    }

    try:
        with lock_driver:
            with SB(uc=True, headless=True) as sb:
                sb.driver.set_page_load_timeout(conf['TIMEOUT'])
                sb.open(url)

                response_url = sb.get_current_url()
                metadata['final_url_raw'] = response_url

                try:
                    sub, dom, tld, path = domains.get_url_parts(response_url)
                    metadata['final_url_domain_tld'] = f"{dom}.{tld}"
                    metadata['final_url_sub_domain_tld'] = f"{sub}.{dom}.{tld}"
                except Exception as e:
                    metadata['error_message'] = f"Domain parsing failed: {e}"

                if metadata['final_url_domain_tld'].lower() != dom_tld.lower():
                    metadata["status_code"] = -1
                    raise Exception("Redirects not allowed by design")

                html = sb.get_page_source()
                metadata['content'] = html.encode("utf-8")
                metadata['status_code'] = 200  # Selenium doesn't return status codes directly

                if filetype_parser.exclude_file_types_from_data(metadata['content']):
                    raise Exception("Unsupported file type")

                metadata['num_bytes_downloaded'] = len(metadata['content'])
                metadata['is_downloaded'] = True
                metadata['has_cookies'] = bool(sb.driver.get_cookies())
                metadata['cookie_names'] = ";".join([c['name'] for c in sb.driver.get_cookies()])
                metadata['browser_version'] = sb.driver.capabilities.get('browserVersion', 'unknown')

    except Exception as e:
        metadata['content'] = None
        metadata['is_downloaded'] = False
        metadata['error_message'] = str(e)

    return metadata
