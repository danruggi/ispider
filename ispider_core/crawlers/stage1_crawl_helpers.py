import time
import re

from ispider_core.utils import domains
from ispider_core.parsers.sitemaps_parser import SitemapParser

from ispider_core import settings

def generic_crawl(c, lock, exclusion_list, fetch_controller, qout):
    rd = c['request_discriminator']
    status_code = c['status_code']
    depth = c['depth']
    dom_tld = c['dom_tld']
    if status_code != 200:
        # If no robot, try with generic sitemap
        if rd == 'robots':
            sitemap_url = domains.add_https_protocol(dom_tld)+"/sitemap.xml"
            with lock:
                fetch_controller[dom_tld] += 1

            qout.put((sitemap_url, 'sitemap', dom_tld, 0, 1))
        return

    if c['content'] is None:
        return

    # if landing and status_code == 200, Add robots.txt
    if rd == 'landing_page':
        if not settings.ROBOTS:
            return

        protfurltld = domains.add_https_protocol(dom_tld);
        robots_url = protfurltld+"/robots.txt"
        
        with lock:
            fetch_controller[dom_tld] += 1

        qout.put((robots_url, 'robots', dom_tld, 0, 1))

    # Add sitemaps from robot file 
    elif rd == 'robots':
        if not settings.SITEMAPS:
            return
        robots_sitemaps = set()
        try:
            for line in str(c['content'], 'utf-8').splitlines():
                if re.search(r'Sitemap[ ]?:', line):
                    sitemap_url = line.split(":", 1)[1].strip();
                    sitemap_url = domains.add_https_protocol(sitemap_url)

                    if sitemap_url in robots_sitemaps:
                        continue
                    robots_sitemaps.add(sitemap_url)

                    with lock:
                        fetch_controller[dom_tld] += 1

                    qout.put((sitemap_url, 'sitemap', dom_tld, 0, 1))
                    c['has_sitemap'] = True;
        except:
            return

    # Add sitemaps from sitemap, deeper depth: 
    elif rd == 'sitemap':
        if not settings.SITEMAPS:
            return
        sm_urls = SitemapParser().extract_sitemap_urls(c['content'], dom_tld)
        count = 0
        for sitemap_url in sm_urls:
            count+=1;
            if depth > settings.SITEMAPS_MAX_DEPTH:
                continue
            with lock:
                fetch_controller[dom_tld] += 1
            qout.put((sitemap_url, 'sitemap', dom_tld, 0, depth+1))
