import asyncio
import json
import time
import os
import re
from datetime import datetime


from ispider_core.crawlers import cls_queue_out
from ispider_core.crawlers import http_client
from ispider_core.crawlers import http_retries
from ispider_core.crawlers import http_filters

from ispider_core.utils import headers
from ispider_core.utils import controllers
from ispider_core.utils import ifiles

from ispider_core.utils.logger import LoggerFactory

from ispider_core.parsers.html_parser import HtmlParser


def call_and_manage_resps(
    reqAL, mod, lock, lock_driver, exclusion_list, seen_filter,
    fetch_controller, totpages_controller, script_controller, conf, logger, hdrs, qout):

    proxy = None
    to = {}

    html_parser = HtmlParser(logger, conf)
    
    ## Fetch the block
    # resps = asyncio.run(http_client.async_main(reqAL, mod, hdrs))
    resps = http_client.fetch_all(reqAL, lock_driver, conf, mod, hdrs)

    for resp in resps:

        # VARIABLE Prepare
        status_code = resp['status_code'];
        url = resp['url']
        rd = resp['request_discriminator']
        dom_tld = resp['dom_tld']
        retries = resp['retries']
        depth = resp['depth']
        error_message = resp['error_message']
        resp['user_agent'] = hdrs['user-agent']
        current_engine = resp['engine']
        sub_dom_tld = resp.get('final_url_sub_domain_tld', dom_tld)

        # SPEED CALC for STATS
        try:
            script_controller['bytes'] += resp['num_bytes_downloaded']
        except:
            pass

        # Crawl FILTERS
        if dom_tld not in fetch_controller:
            continue

        try:
            http_filters.filter_on_resp(resp)
        except Exception as e:
            logger.error(e)
            controllers.reduce_fetch_controller(fetch_controller, lock, dom_tld)
            continue

        # CHECK IF FILE EXISTS
        try:
            http_filters.filter_file_exists(resp, conf)
        except Exception as e:
            logger.error(e)
            controllers.reduce_fetch_controller(fetch_controller, lock, dom_tld)
            continue

        # **********************
        # ERROR CORRECTION / RETRIES
        if http_retries.should_retry(resp, conf, logger, qout, mod):
            continue


        # if status_code != 200:
        logger.debug(f"[{mod}] [{status_code}] -- D:{depth} -- R: {retries} -- [{dom_tld}] {url}")

        # ***********************
        # NEXT ACTIONS MANAGEMENT
        # ALL - LEVEL 1
        
        # FILTER
        if depth + 1 <= conf['WEBSITES_MAX_DEPTH']:
            links = html_parser.extract_urls_from_content(dom_tld, sub_dom_tld, resp['content'])
            
            regexes = [re.compile(p) for p in conf['EXCLUDED_EXPRESSIONS_URL']]
            links = [
                link for link in links
                if not any(regex.search(link) for regex in regexes)
            ]

            with lock:
                current_total = totpages_controller[dom_tld] 
            
            remaining = conf['MAX_PAGES_POR_DOMAIN'] - current_total
            if remaining <= 0:
                links = []
            elif len(links) > remaining:
                links = links[:remaining]  # Limit to remaining space

            with lock:
                fetch_controller[dom_tld] += len(links)
                totpages_controller[dom_tld] += len(links)

                for link in links:
                    qout.put((link, 'internal_url', dom_tld, 0, depth+1, current_engine))

        try:
            reduced_reqA = seen_filter.resp_to_req(resp)
            seen_filter.add_to_seen_req(reduced_reqA)
        except Exception as e:
            logger.error(e)

        # Reduce dom count Up Down by 1
        controllers.reduce_fetch_controller(fetch_controller, lock, dom_tld)

        ### DUMP To file AND Delete content from resp
        # if resp['content'] is not None:
        resp['page_size'] = len(resp['content']) if resp['content'] is not None else 0;
        resp['is_downloaded'] = ifiles.dump_to_file(resp, conf)

        del(resp['content'])
        
        dump_fname = os.path.join(conf['path_jsons'], f"spider_conn_meta.{mod}.json")
        with open(dump_fname, 'a+') as f:
            json.dump(resp, f)
            f.write('\n')

        ## 50MB    
        if os.path.getsize(dump_fname) > conf['MAX_CRAWL_DUMP_SIZE']:
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            back_dump_fname = os.path.join(conf['path_jsons'], f"spider_conn_meta.{mod}.{current_time}.json")
            os.replace(dump_fname, back_dump_fname)

def spider(mod, conf, exclusion_list, seen_filter,
        counter, lock, lock_driver, 
        script_controller, fetch_controller, totpages_controller,
        qin, qout
    ):
    
    '''
    ** counter: Integer with general counter
    ** dwn_list [shared_dwn_list]: All downloaded list
    ** script_controller: dict with specific counters for crawling: Landing, Robots, Sitemaps, bytes, priority
    ** fetch_controller: dom_tld based controller with (UpDownInt, time_last_fetched)
    ** q: shared queue
    '''
    # from libs.dump_files import dumpToFile
    logger = LoggerFactory.create_logger(
                "./logs", "stage_spider.log",
                log_level=conf['LOG_LEVEL'],
                stdout_flag=True
            )

    tot_workers = conf['POOLS']

    out = list()
    urls = list()

    # MAIN Cycle of crawling
    script_controller['running_state'] = 9;

    # try:
    t0 = time.time()
    times=list()

    hdrs = headers.get_header('basics')

    while True:
        try:
            reqA = qin.get(timeout=60)
        except:
            break

        url = reqA[0]
        rd = reqA[1]
        dom_tld = reqA[2]
        if dom_tld in exclusion_list:
            reduceFetchController(fetch_controller, lock, dom_tld)
            logger.debug(f"{dom_tld} excluded {url}")
            continue

        urls.append(reqA)
        
        if len(urls) >= conf['ASYNC_BLOCK_SIZE'] or qin.qsize() == 0:
            call_and_manage_resps(urls, mod, lock, lock_driver, exclusion_list, seen_filter, fetch_controller, totpages_controller, script_controller, conf, logger, hdrs, qout)
            with lock:
                counter.value += len(urls)

            # ppprint("Set urls empty")
            urls = list()

    if len(urls) > 0:
        try:
            logger.info(f"[Worker {mod}] Last call")
            call_and_manage_resps(urls, mod, lock, lock_driver, exclusion_list, seen_filter, fetch_controller, totpages_controller, script_controller, conf, logger, hdrs, qout)
        except Exception as e:
            logger.error(f"ERR000F Last call main call_and_manage_resps error {e}")

    q = None;
    logger.info(f"[Worker {mod}] Finished")
    return None
