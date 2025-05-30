from bs4 import BeautifulSoup
import time
import re
import urllib.parse

from ispider_core.utils import domains
from ispider_core.utils.logger import LoggerFactory

from w3lib.url import canonicalize_url, safe_url_string
import tldextract

class HtmlParser:
    def __init__(self, logger, conf):
        self.logger = logger
        self.conf = conf

    def extract_urls(self, dom_tld, fpath):
        """Reads an HTML file and extracts URLs."""
        try:
            with open(fpath, 'r', errors='ignore') as fp:
                html_content = fp.read()
        except Exception as e:
            self.logger.error(f"Error reading file {fpath}: {e}")
            return set()

        return self.extract_urls_from_content(dom_tld, dom_tld, html_content)

    def extract_urls_from_content(self, dom_tld, sub_dom_tld, html_content):
        """Extracts URLs from raw HTML content."""
        all_href = set()
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except:
            return set()
        for link in soup.find_all('a', href=True):
            try:
                href = link['href'].strip().lower()
                href_cleaned = self._clean_href(dom_tld, sub_dom_tld, href)
                href_cleaned = domains.add_https_protocol(href_cleaned)
                all_href.add(href_cleaned)
            except Exception as e:
                if not str(e).startswith('SKIP'):
                    self.logger.debug(f"Skipping URL DOM: {dom_tld} -- {href}: {e}")
                continue

        return all_href

    def _clean_href(self, dom_tld, sub_dom_tld, x):
        """Cleans and normalizes a given href URL."""
        x0 = x
        x = x.strip()

        if x.startswith("#"):
            raise Exception("SKIP001: Hash url: " + str(x))
        if x.startswith('//'):
            x = x.lstrip('/')
        if x == "/":
            raise Exception("SKIP002: Home url: " + str(x))
        if any(prefix in x.lower() for prefix in ['javascript:', 'tel:', 'mailto:']):
            raise Exception("SKIP003: Invalid protocol: " + str(x))
        if not re.search(r'[0-9a-zA-Z]', x):
            raise Exception("SKIP004: Invalid url: " + str(x))

        if x.startswith("./"):
            x = x.strip(".")
        if x.startswith("../"):
            x = x.replace('../', '')

        if x.startswith("/") or x.startswith("?"):
            x = sub_dom_tld + x
        elif x.startswith("http"):
            x = re.sub(r'http[s]?://', '', x)
        elif "/" not in x:
            x = sub_dom_tld + "/" + x
        elif "/" in x and "." not in x.split("/")[0]:
            x = sub_dom_tld + "/" + x
        elif re.search(r'[a-z0-9]\.(?:php|html)\?.*=', x):
            x = sub_dom_tld + "/" + x

        try:
            href_uparsed = urllib.parse.urlparse("//" + x)
            href_dom = href_uparsed.netloc
            href_pat = href_uparsed.path.strip("/")
            href_que = href_uparsed.query
        except Exception as e:
            raise Exception("SKIP005: Href urlparse error:" + str(e))

        sub, dom, tld, path = domains.get_url_parts(href_dom)
        href_dom_tld = dom + "." + tld

        if "%" in href_pat:
            href_pat = urllib.parse.unquote(href_pat)

        if re.search(r'\.[a-z0-9]{3,4}$', href_pat.lower()):
            ext = re.search(r'\.([a-z0-9]{3,4})$', href_pat.lower()).group(1)
            if ext in self.conf['EXCLUDED_EXTENSIONS']:
                raise Exception("SKIP006: Excluded Extension: " + str(ext))

        if re.search(r'=[a-zA-Z0-9_]+\.jpg', href_que.lower()):
            raise Exception("SKIP007: Jpg in query")

        if re.search(r'[a-zA-Z0-9]', sub) and sub != 'www':
            href_cleaned = sub + "." + dom + '.' + tld + "/" + href_pat
        else:
            href_cleaned = dom + '.' + tld + "/" + href_pat

        if href_que:
            href_cleaned += "?" + href_que

        if re.search(r'(?:www\.)?(?:' + re.escape(dom_tld) + r'|' + re.escape(sub_dom_tld) + r')/?$', href_cleaned):
            raise Exception("SKIP008: Home URL FINAL --> " + str(href_cleaned))

        if href_dom_tld != dom_tld:
            raise Exception("SKIP009: External Domain: " + str(x))

        return href_cleaned

    def _clean_href_modern(self, dom_tld, href):
        """Cleans and normalizes a given href URL."""
        if not href or href.startswith(('#', 'javascript:', 'tel:', 'mailto:')):
            raise Exception("SKIP010: Invalid or unsupported URL: " + href)

        href = safe_url_string(href.strip())

        if href.startswith('//'):
            href = 'http:' + href  # Assume http if protocol is missing

        parsed_url = urllib.parse.urlparse(href)
        extracted = tldextract.extract(parsed_url.netloc)

        if not extracted.domain:
            href = urllib.parse.urljoin(dom_tld, href)
            parsed_url = urllib.parse.urlparse(href)
            extracted = tldextract.extract(parsed_url.netloc)

        href_cleaned = canonicalize_url(parsed_url.geturl())

        if extracted.registered_domain != dom_tld:
            raise Exception("SKIP011: External Domain: " + href)

        if any(href.endswith(ext) for ext in self.conf['EXCLUDED_EXTENSIONS']):
            raise Exception("SKIP012: Excluded Extension: " + href)

        return href_cleaned
