import os
import time
import validators
import json

from queue import Queue
from ispider_core.utils import domains
from ispider_core.utils import engine

from ispider_core.parsers.html_parser import HtmlParser
from ispider_core.parsers.sitemaps_parser import SitemapParser

class QueueOut:
    def __init__(self, conf, dom_stats, dom_tld_finished, exclusion_list, logger, q):
        self.conf = conf
        self.logger = logger
        self.dom_stats = dom_stats
        self.dom_tld_finished = dom_tld_finished
        self.exclusion_list = exclusion_list
        self.tot_finished = len(dom_tld_finished)
        self.engine_selector = engine.EngineSelector(conf['ENGINES'])
        self.q = q

    def fullfill_q(self, url, dom_tld, rd, depth=0, engine='httpx'):
        self.dom_stats.add_missing_total(dom_tld)
        reqA = (url, rd, dom_tld, 0, depth, engine)
        self.q.put(reqA)


    def fullfill(self, stage):
        t0 = time.time()

        total = len(self.conf['domains'])
        self.logger.info(f"[{stage}] Fullfill the queue for {total} domains")
        processed = 0

        for url in self.conf['domains']:
            try:
                if not url:
                    continue

                processed += 1
                percent = round((processed / total) * 100, 2)

                if processed % max(1, total // 20) == 0:
                    self.logger.info(f"Progress: {percent}% ({processed}/{total})")

                sub, dom, tld, path = domains.get_url_parts(url)
                dom_tld = f"{dom}.{tld}"
                url = domains.add_https_protocol(dom_tld)

                if dom in self.exclusion_list or dom_tld in self.exclusion_list:
                    self.logger.warning(f'{url} excluded for domain exclusion')
                    continue

                # Check if domain already exists (considering redirects)
                final_dom_tld = self.dom_stats.get_final_domain(dom_tld)
                if final_dom_tld in self.dom_stats.dom_missing:
                    # self.logger.debug(f'{dom_tld} already in queue (or redirected to {final_dom_tld})')
                    continue
                    
                if not validators.domain(dom_tld):
                    self.logger.info(f"{url} not valid domain")
                    continue

                # Check if the domain (or its redirect target) is finished
                if dom_tld in self.dom_tld_finished or final_dom_tld in self.dom_tld_finished:
                    self.logger.info(f'{url} already finished (original or redirect target)')
                    self.tot_finished += 1
                    continue

                # Add the domain with its original name
                self.dom_stats.add_domain(dom_tld)
                self.logger.debug(f"Added {dom_tld}")
                self.fullfill_q(url, dom_tld, rd='landing_page', depth=0, engine=self.engine_selector.next())

            except Exception as e:
                self.logger.error(e)
                continue

        try:
            tt = round((time.time() - t0), 5)
            self.logger.info(f"Queue Fullfilled, QSize: {self.q.qsize()} [already finished: {str(self.tot_finished)}]")
            self.logger.info(f"Tot Time [s]: {tt} -- Fullfilling rate [url/s]: {round((self.q.qsize() / tt), 2)}")

        except Exception as e:
            self.logger.error(f"Stats Unavailable {e}")


    def get_queue(self):
        return self.q
        
