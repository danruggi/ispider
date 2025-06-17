
import asyncio
import json
import time
import os
import re
from datetime import datetime
from queue import Empty

from ispider_core.crawlers import http_client
from ispider_core.crawlers import http_filters
from ispider_core.crawlers import http_retries
from ispider_core.crawlers import stage_crawl_helpers
from ispider_core.crawlers import stage_unified_helpers

from ispider_core.utils.logger import LoggerFactory
from ispider_core.utils import headers
from ispider_core.utils import ifiles
from ispider_core.utils import domains

from ispider_core.parsers.html_parser import HtmlParser
from ispider_core.parsers.sitemaps_parser import SitemapParser


def call_and_manage_resps(
    reqAL, mod, lock_driver, exclusion_list, seen_filter,
    dom_stats, script_controller, conf, logger, hdrs, qout):

    html_parser = HtmlParser(logger, conf)
    
    ## Fetch the block
    resps = http_client.fetch_all(reqAL, lock_driver, conf, mod, hdrs)
    
    for resp in resps:
        # VARIABLE Prepare
        status_code = resp['status_code']
        url = resp['url']
        rd = resp['request_discriminator']
        dom_tld = resp['dom_tld']
        retries = resp['retries']
        depth = resp['depth']
        error_message = resp['error_message']
        current_engine = resp['engine']
        resp['user_agent'] = hdrs['user-agent']
        sub_dom_tld = resp.get('final_url_sub_domain_tld', dom_tld)

        # SPEED CALC for STATS
        try:
            script_controller['bytes'] += resp['num_bytes_downloaded']
            dom_stats.qstats.put({"dom_tld": dom_tld, "key": "bytes", "value": resp['num_bytes_downloaded'], "op": "sum"})
        except Exception as e:
            logger.warning(e)
            pass

        # Crawl FILTERS
        if dom_tld not in dom_stats.dom_missing:
            logger.warning(f"{dom_tld} not in fetch controller")
            continue

        try:
            http_filters.filter_on_resp(resp)
        except Exception as e:
            logger.warning(f"{e}")
            dom_stats.reduce_missing(dom_tld)
            continue

        ## CHECK IF FILE EXISTS
        try:
            http_filters.filter_file_exists(resp, conf)
        except Exception as e:
            logger.error(e)
            dom_stats.reduce_missing(dom_tld)
            continue

        # **********************
        # ERROR CORRECTION / RETRIES
        if http_retries.should_retry(resp, conf, logger, qout, mod):
            continue
        
        logger.debug(f"[{mod}] [{status_code}] -- D:{depth} -- R: {retries} -- E:{current_engine} -- [{dom_tld}] {url}")

        # ***********************
        # UNIFIED ACTIONS MANAGEMENT
        try:
            # Handle crawl stage actions (robots, sitemaps)
            stage_crawl_helpers.robots_sitemaps_crawl(
                resp, dom_stats, current_engine, conf, logger, qout)
        
            # Extract links from sitemaps and internal_urls
            stage_unified_helpers.unified_link_extraction(
                resp, dom_stats, qout, conf, logger, current_engine)

        except Exception as e:
            logger.error(f"Unified processing error for {url}: {e}")

        # Add to seen filter
        try:
            reduced_reqA = seen_filter.resp_to_req(resp)
            seen_filter.add_to_seen_req(reduced_reqA)
        except Exception as e:
            logger.error(e)

        # Reduce dom count Up Down by 1
        dom_stats.reduce_missing(dom_tld)

        ### DUMP To file AND Delete content from resp
        resp['page_size'] = len(resp['content']) if resp['content'] is not None else 0
        resp['is_downloaded'] = ifiles.dump_to_file(resp, conf)

        del(resp['content'])
        
        dump_fname = os.path.join(conf['path_jsons'], f"unified_conn_meta.{mod}.json")
        with open(dump_fname, 'a+') as f:
            json.dump(resp, f)
            f.write('\n')

        ## 50MB    
        if os.path.getsize(dump_fname) > conf['MAX_CRAWL_DUMP_SIZE']:
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            back_dump_fname = os.path.join(conf['path_jsons'], f"unified_conn_meta.{mod}.{current_time}.json")
            os.replace(dump_fname, back_dump_fname)


def unified(mod, conf, exclusion_list, seen_filter, 
        lock, lock_driver, 
        script_controller, dom_stats,
        qin, qout):
    
    '''
    Unified stage that combines crawl and spider functionality:
    - Crawls landing pages, robots.txt, sitemaps
    - Extracts all links from HTML content and sitemaps
    - Adds extracted links to queue with 'internal_url' discriminator
    
    ** counter: Integer with general counter
    ** script_controller: dict with specific counters
    ** dom_missing: dom_tld based controller
    ** qin: input queue
    ** qout: output queue
    '''
    
    logger = LoggerFactory.create_logger(conf, "ispider.log", stdout_flag=True)

    urls = list()

    # MAIN Cycle of unified processing
    script_controller['running_state'] = 9
    script_controller.update({
        'landings': 0, 
        'robots': 0, 
        'sitemaps': 0, 
        'internal_urls': 0
    })

    t0 = time.time()
    hdrs = headers.get_header('basics')

    try:

        while script_controller['running_state']:
            try:
                reqA = qin.get(timeout=10)
            except Empty:
                continue

            url = reqA[0]
            rd = reqA[1]
            dom_tld = reqA[2]
            
            if dom_tld in exclusion_list:
                dom_stats.reduce_missing(dom_tld)
                logger.warning(f"{dom_tld} excluded {url}")
                continue
                
            urls.append(reqA)
            
            if len(urls) >= conf['ASYNC_BLOCK_SIZE'] or qin.qsize() == 0:
                call_and_manage_resps(
                    urls, mod, lock_driver, exclusion_list, seen_filter, 
                    dom_stats, script_controller, 
                    conf, logger, hdrs, qout)
                
                with lock:
                    script_controller['tot_counter'] += len(urls)
                
                urls = list()

    except KeyboardInterrupt:
        logger.warning("Subprocess interrupted by keyboard")

    logger.debug(f"Closing worker {mod}")
    
    return None