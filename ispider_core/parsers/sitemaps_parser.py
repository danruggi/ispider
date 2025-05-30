import re
import gzip

from xml.etree.ElementTree import ElementTree, fromstring
from urllib.parse import urlparse


class SitemapParser:
    def __init__(self, logger, conf):
        self.logger = logger
        self.conf = conf

    def _get_ns(self, root):
        """Extract XML namespace from the root element."""
        match = re.match(r'\{.*\}', root.tag)
        return match.group(0) if match else ""

    def _decompress_gzip(self, data):
        """Decompress GZipped content."""
        if data[:2] == b'\x1f\x8b':  # GZip signature
            try:
                return gzip.decompress(data)
            except Exception as e:
                self.logger.error(f"Failed to decompress GZip: {e}")
                return None
        return data

    def _extract_links_from_xml(self, data, tag):
        """
        Extract links from XML or TXT sitemaps.
        This is the old get_links_from_xml
        """
        if not data or len(data) > self.conf['MAX_CRAWL_DUMP_SIZE']:
            self.logger.warning("Sitemap too big or empty, skipping...")
            return set()

        # print(data)
        if data.decode('utf-8', errors='ignore').lstrip().lower().startswith("<!doctype html>"):
            return set()

        try:
            tree = ElementTree(fromstring(data))
            root = tree.getroot()
            ns = self._get_ns(root)

            return {url.find(f"{ns}loc").text for url in root.iter(f"{ns}{tag}") if url.find(f"{ns}loc") is not None}
        except Exception:
            return self._extract_links_from_txt(data)

    def _extract_links_from_txt(self, data):
        """Extract links from a plain TXT sitemap."""
        out = set()
        for line in data.decode(errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("http"):
                out.add(line)
        return out

    def extract_sitemap_urls(self, sm_data, dom_tld):
        """Extract sitemap URLs from sitemap content."""
        sm_data = self._decompress_gzip(sm_data)
        if sm_data is None:
            return []

        sitemap_links = self._extract_links_from_xml(sm_data, 'sitemap')
        return self._filter_same_domain(sitemap_links, dom_tld)

    def extract_all_links(self, sm_data):
        """Extract all URLs (not just sitemaps) from XML/TXT content."""
        sm_data = self._decompress_gzip(sm_data)
        if sm_data is None:
            return []

        return list(self._extract_links_from_xml(sm_data, 'url'))

    def _filter_same_domain(self, urls, dom_tld):
        """Filter out links that do not belong to the same domain."""
        valid_urls = set()
        for url in urls:
            parsed = urlparse(url)
            domain_parts = parsed.netloc.split(".")
            if len(domain_parts) >= 2:
                sm_dom_tld = ".".join(domain_parts[-2:])
                if sm_dom_tld == dom_tld:
                    valid_urls.add(url)
                # else:
                #     self.logger.warning(f"Sitemap found in different domain: {dom_tld} --> {url}")
        return list(valid_urls)
