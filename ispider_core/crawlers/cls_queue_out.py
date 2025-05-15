import os
import time
import validators
from queue import Queue
from ispider_core.utils import domains
from ispider_core.utils.logger import LoggerFactory

from ispider_core.parsers.html_parser import HtmlParser
from ispider_core.parsers.sitemaps_parser import SitemapParser

from ispider_core import settings

class QueueOut:
    def __init__(self, conf, fetch_controller, dom_tld_finished, exclusion_list, q):
        self.conf = conf
        self.logger = LoggerFactory.create_logger(
                    "./logs", "queue_out.log",
                    log_level=settings.LOG_LEVEL,
                    stdout_flag=True
                )
        self.fetch_controller = fetch_controller
        self.dom_tld_finished = dom_tld_finished
        self.exclusion_list = exclusion_list
        self.tot_finished = 0
        self.q = q

    def fullfill_q(self, url, dom_tld, rd, d=0):
        self.fetch_controller[dom_tld] += 1
        reqA = (url, rd, dom_tld, 0, d)
        self.q.put(reqA)

    def fullfill_q_all_links(self, all_links, dom_tld):
        for link in all_links:
            self.fullfill_q(link, dom_tld, rd='internal_url', d=1)

    def stage2_all_links(self, dom_tld):
        # read all avail files and load urls
        rel_path = os.path.join(self.conf['path_dumps'], dom_tld)

        if not os.path.isdir(rel_path):
            raise Exception("dom_tld directory not found")
        all_links = set()
        tot_landings=0
        tot_sitemaps=0
        for f in os.scandir(rel_path):
            links = []
            if f.name == '_.html':
                # Landing
                links = HtmlParser(
                    ).extract_urls(dom_tld, f.path)
                tot_landings+=len(links)
            elif f.name != 'robots.txt' and not f.name.endswith('.html'):
                # Sitemaps
                with open(f.path, 'rb') as file:
                    links = SitemapParser(
                        ).extract_all_links(file.read())
                tot_sitemaps+=len(links)

            if links is not None:
                links = {domains.add_https_protocol(x) for x in links}
                all_links = all_links.union(links)
        return all_links

    def fullfill(self, stage):
        t0 = time.time()

        for url in self.conf['domains']:
            # self.logger.info(url)
            try:
                if not url:
                    continue

                sub, dom, tld, path = domains.get_url_parts(url)
                dom_tld = f"{dom}.{tld}"
                url = domains.add_https_protocol(dom_tld)

                if dom in self.exclusion_list or dom_tld in self.exclusion_list:
                    continue

                if dom_tld in self.fetch_controller:
                    continue

                self.fetch_controller[dom_tld] = 0

                if not validators.domain(dom_tld):
                    continue

                if dom_tld in self.dom_tld_finished:
                    self.tot_finished += 1
                    continue

                if stage == 'stage1':
                    self.fullfill_q(url, dom_tld, rd='landing_page', d=0)
                elif stage == 'stage2':
                    all_links = self.stage2_all_links(dom_tld)
                    self.fullfill_q_all_links(all_links, dom_tld)

                if self.tot_inserted % 50000 == 0:
                    self.logger.info(f"Tot inserted: {self.tot_inserted} in time: {round((time.time()-t0), 2)}")
            except:
                continue

        try:
            tt = round((time.time() - t0), 5)
            self.logger.info(f"Queue Fullfilled, QSize: {self.q.qsize()} [already finished: {str(self.tot_finished)}]")
            self.logger.info(f"Tot Time [s]: {tt} -- Fullfilling rate [url/s]: {round((self.q.qsize() / tt), 2)}")
        except Exception as e:
            self.logger.error(f"Stats Unavailable {e}")

    def get_queue(self):
        return self.q
