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