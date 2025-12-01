import re
from ispider_core.parsers.html_parser import HtmlParser
from ispider_core.parsers.sitemaps_parser import SitemapParser
from ispider_core.utils import domains

def extract_and_queue_html_links(c, dom_stats, qout, conf, logger, current_engine):
    """Extract links from HTML content and add them to the queue"""
    rd = c['request_discriminator']
    status_code = c['status_code']
    depth = c['depth']
    dom_tld = c['dom_tld']
    sub_dom_tld = c.get('sub_dom_tld', dom_tld)
    
    if status_code != 200 or c['content'] is None:
        return
    
    if rd not in ['landing_page', 'internal_url']:
        return
        
    if depth + 1 > conf['WEBSITES_MAX_DEPTH']:
        return
    
    # Extract links from HTML content
    html_parser = HtmlParser(logger, conf)
    links = html_parser.extract_urls_from_content(dom_tld, sub_dom_tld, c['content'])

    # Apply URL exclusion filters
    regexes = [re.compile(p) for p in conf['EXCLUDED_EXPRESSIONS_URL']]
    links = [
        link for link in links
        if not any(regex.search(link) for regex in regexes)
    ]

    links = dom_stats.filter_and_add_links(dom_tld, links, conf['MAX_PAGES_POR_DOMAIN'])
    for link in links:
        # print(link)
        qout.put((link, 'internal_url', dom_tld, 0, depth+1, current_engine))


def extract_and_queue_sitemap_links(c, dom_stats, qout, conf, logger, current_engine):
    """Extract links from sitemap content and add them to the queue"""
    rd = c['request_discriminator']
    status_code = c['status_code']
    depth = c['depth']
    dom_tld = c['dom_tld']

    if status_code != 200 or c['content'] is None:
        return

    if rd != 'sitemap':
        return

    # Extract links from sitemap content
    smp = SitemapParser(logger, conf)
    sitemap_links = smp.extract_all_links(c['content'])

    links = dom_stats.filter_and_add_links(dom_tld, sitemap_links, conf['MAX_PAGES_POR_DOMAIN'])
    for link in links:
        link_with_protocol = domains.add_https_protocol(link)
        qout.put((link_with_protocol, 'internal_url', dom_tld, 0, depth + 1, current_engine))


def unified_link_extraction(c, dom_stats, qout, conf, logger, current_engine):
    """Unified function to handle both HTML and sitemap link extraction"""
    extract_and_queue_html_links(c, dom_stats, qout, conf, logger, current_engine)
    extract_and_queue_sitemap_links(c, dom_stats, qout, conf, logger, current_engine)

def increase_script_controller_counters(rd, script_controller, lock):
    
    with lock:
        if rd == "landing":
            script_controller["landings"] = script_controller.get("landings", 0) + 1
        elif rd == "robots":
            script_controller["robots"] = script_controller.get("robots", 0) + 1
        elif rd == "sitemap":
            script_controller["sitemaps"] = script_controller.get("sitemaps", 0) + 1
        elif rd == "internal_url":
            script_controller["internal_urls"] = script_controller.get("internal_urls", 0) + 1

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
                if re.search(r'sitemap\s*:', line, re.IGNORECASE):
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

    
