import os
import time
import validators
import json

from queue import Queue
from ispider_core.utils import domains
from ispider_core.utils import engine
from ispider_core.utils.logger import LoggerFactory

from ispider_core.parsers.html_parser import HtmlParser
from ispider_core.parsers.sitemaps_parser import SitemapParser

class QueueOut:
    def __init__(self, conf, fetch_controller, totpages_controller,dom_tld_finished, exclusion_list, q):
        self.conf = conf
        self.logger = LoggerFactory.create_logger(
                    "./logs", "queue_out.log",
                    log_level=conf['LOG_LEVEL'],
                    stdout_flag=True
                )
        self.fetch_controller = fetch_controller
        self.totpages_controller = totpages_controller
        self.dom_tld_finished = dom_tld_finished
        self.exclusion_list = exclusion_list
        self.tot_finished = 0
        self.engine_selector = engine.EngineSelector(conf['ENGINES'])
        self.q = q

    def fullfill_q(self, url, dom_tld, rd, depth=0, engine='httpx'):
        self.fetch_controller[dom_tld] += 1
        self.totpages_controller[dom_tld] += 1
        reqA = (url, rd, dom_tld, 0, depth, engine)
        self.q.put(reqA)

    def fullfill_q_all_links(self, all_links, dom_tld, engine='httpx'):
        for link in all_links:
            self.fullfill_q(link, dom_tld, rd='internal_url', depth=1, engine=engine)

    def all_links(self, dom_tld, stage):
        jsons_path = self.conf['path_jsons']

        all_links = set()
        tot_landings = 0
        tot_sitemaps = 0
        landing_done = False

        if os.path.isdir(jsons_path):
            for entry in os.listdir(jsons_path):
                if not entry.startswith("crawl_conn_meta.") or not entry.endswith(".json"):
                    continue

                json_file = os.path.join(jsons_path, entry)
                with open(json_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                            if obj.get("dom_tld") != dom_tld or not obj.get("is_downloaded"):
                                continue

                            discr = obj.get("request_discriminator")

                            if discr == "sitemap" and obj.get("sitemap_fname"):
                                sitemap_file = os.path.join(self.conf['path_dumps'], obj["sitemap_fname"])
                                if os.path.isfile(sitemap_file):
                                    with open(sitemap_file, 'rb') as sf:
                                        smp =  SitemapParser(self.logger, self.conf, )
                                        links = smp.extract_all_links(sf.read())
                                        all_links |= {domains.add_https_protocol(x) for x in links}
                                        tot_sitemaps += len(links)

                            elif discr == "landing_page" and not landing_done:
                                # Try to guess the landing HTML file
                                # Try from sitemap_fname if present
                                rel_path = os.path.join(self.conf['path_dumps'], dom_tld)
                                landing_file = os.path.join(rel_path, '_.html')

                                if os.path.isfile(landing_file):
                                    hp = HtmlParser(self.logger, self.conf, )
                                    links = hp.extract_urls(dom_tld, landing_file)
                                    all_links |= {domains.add_https_protocol(x) for x in links}
                                    tot_landings += len(links)
                                    landing_done = True

                        except json.JSONDecodeError:
                            self.logger.warning(f"Invalid JSON in {json_file}: {line[:80]}...")
                        except Exception as e:
                            self.logger.error(f"Error processing entry in {json_file}: {e}")

        # self.logger.info(f"Total links from landings: {tot_landings}, sitemaps: {tot_sitemaps}")
        return all_links

    def fullfill(self, stage):
        t0 = time.time()

        total = len(self.conf['domains'])
        self.logger.info(f"[{stage}] Fullfill the queue for {total} domains")
        processed = 0

        for url in self.conf['domains']:
            # self.logger.info(url)
            try:
                if not url:
                    continue

                processed += 1
                percent = round((processed / total) * 100, 2)

                if processed % max(1, total // 20) == 0:  # Log every ~5% steps
                    self.logger.info(f"Progress: {percent}% ({processed}/{total})")

                sub, dom, tld, path = domains.get_url_parts(url)
                dom_tld = f"{dom}.{tld}"
                url = domains.add_https_protocol(dom_tld)

                if dom in self.exclusion_list or dom_tld in self.exclusion_list:
                    self.logger.warning(f'{url} excluded for domain exclusion')
                    continue

                if dom_tld in self.fetch_controller:
                    continue
                self.fetch_controller[dom_tld] = 0

                if dom_tld in self.totpages_controller:
                    continue
                self.totpages_controller[dom_tld] = 0

                if not validators.domain(dom_tld):
                    self.logger.info(f"{url} not valid domain")
                    continue

                if dom_tld in self.dom_tld_finished:
                    # self.logger.warning(f'{url} already finished')
                    self.tot_finished += 1
                    continue

                # self.logger.info(stage)
                if stage == 'crawl':
                    self.fullfill_q(url, dom_tld, rd='landing_page', depth=0, engine=self.engine_selector.next())

                elif stage == 'spider':
                    all_links = self.all_links(dom_tld, stage)
                    self.fullfill_q_all_links(all_links, dom_tld, engine=self.engine_selector.next())
                    
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
