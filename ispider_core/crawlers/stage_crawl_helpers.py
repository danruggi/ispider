import time
import re

from ispider_core.utils import domains
from ispider_core.parsers.sitemaps_parser import SitemapParser

def robots_sitemaps_crawl(c, dom_stats, engine, conf, logger, qout):
    rd = c['request_discriminator']
    status_code = c['status_code']
    depth = c['depth']
    dom_tld = c['dom_tld']
    if status_code != 200:
        # If no robot, try with generic sitemap
        if rd != 'robots':
            return
        if 'sitemaps' not in conf['CRAWL_METHODS']:
            return
        sitemap_url = domains.add_https_protocol(dom_tld)+"/sitemap.xml"
        dom_stats.add_missing_total(dom_tld)
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
        
        dom_stats.add_missing_total(dom_tld)
        qout.put((robots_url, 'robots', dom_tld, 0, 1, engine))

    # Add sitemaps from robot file 
    elif rd == 'robots':
 
        dom_stats.qstats.put({"dom_tld": dom_tld, "key": "has_robot", "value": True, "op": "set"})
 
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
                    dom_stats.add_missing_total(dom_tld)
                    qout.put((sitemap_url, 'sitemap', dom_tld, 0, 1, engine))
                    c['has_sitemap'] = True;
        except:
            return

    # Add sitemaps from sitemap, deeper depth: 
    elif rd == 'sitemap':
        dom_stats.qstats.put({"dom_tld": dom_tld, "key": "has_sitemaps", "value": True, "op": "set"})
        smp =  SitemapParser(logger, conf)
        sm_urls = smp.extract_sitemap_urls(c['content'], dom_tld)
        for sitemap_url in sm_urls:
            if depth > conf['SITEMAPS_MAX_DEPTH']:
                continue
            dom_stats.add_missing_total(dom_tld)
            qout.put((sitemap_url, 'sitemap', dom_tld, 0, depth+1, engine))
