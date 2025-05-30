import time
import re

from ispider_core.utils import domains
from ispider_core.parsers.sitemaps_parser import SitemapParser

def robots_sitemaps_crawl(c, lock, exclusion_list, fetch_controller, engine, conf, logger, qout):
    rd = c['request_discriminator']
    status_code = c['status_code']
    depth = c['depth']
    dom_tld = c['dom_tld']
    if status_code != 200:
        # If no robot, try with generic sitemap
        if rd == 'robots':
            if 'sitemaps' not in conf['CRAWL_METHODS']:
                return
            sitemap_url = domains.add_https_protocol(dom_tld)+"/sitemap.xml"
            with lock:
                fetch_controller[dom_tld] += 1

            qout.put((sitemap_url, 'sitemap', dom_tld, 0, 1, engine))
        return

    if c['content'] is None:
        return

    # if landing and status_code == 200, Add robots.txt
    if rd == 'landing_page':
        if 'robots' not in conf['CRAWL_METHODS']:
            return

        protfurltld = domains.add_https_protocol(dom_tld);
        robots_url = protfurltld+"/robots.txt"
        
        with lock:
            fetch_controller[dom_tld] += 1

        qout.put((robots_url, 'robots', dom_tld, 0, 1, engine))

    # Add sitemaps from robot file 
    elif rd == 'robots':
        if 'sitemaps' not in conf['CRAWL_METHODS']:
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

                    qout.put((sitemap_url, 'sitemap', dom_tld, 0, 1, engine))
                    c['has_sitemap'] = True;
        except:
            return

    # Add sitemaps from sitemap, deeper depth: 
    elif rd == 'sitemap':
        
        smp =  SitemapParser(logger, conf)
        sm_urls = smp.extract_sitemap_urls(c['content'], dom_tld)
        count = 0
        for sitemap_url in sm_urls:
            count+=1;
            if depth > conf['SITEMAPS_MAX_DEPTH']:
                continue
            with lock:
                fetch_controller[dom_tld] += 1
            qout.put((sitemap_url, 'sitemap', dom_tld, 0, depth+1, engine))
