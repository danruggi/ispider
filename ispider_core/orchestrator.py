import time
import json
import multiprocessing
from ispider_core.utils.logger import LoggerFactory

class Orchestrator:
    def __init__(self, conf, manager=None, shared_counter=None):
        """
        Initialize the orchestrator with configurations.
        :param conf: Configuration dictionary.
        :param manager: Multiprocessing manager.
        :param shared_counter: Shared counter object.
        """
        self.conf = conf
        self.manager = manager or multiprocessing.Manager()
        self.shared_counter = shared_counter or self.manager.Value('i', 0)

        # Initialize logger
        self.logger = LoggerFactory.create_logger(
            "./logs", "Orchestrator.log",
            log_level='DEBUG',
            stdout_flag=True
        )

    def run(self):
        """
        Executes the correct function based on the METHOD.
        """
        start_time = time.time()
        self.logger.info(f"*** BEGIN METHOD {self.conf['method']} ***")

        # Execute the correct module based on METHOD
        self._execute_method()

        # Timing statistics
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        avg_speed = round(self.shared_counter.value / duration, 2) if duration > 0 else 0

        self.logger.info(
            f"*** ENDS method {self.conf['method']} - Stats: {self.shared_counter.value} items in {duration}s; "
            f"Average speed: {avg_speed} items/s ***"
        )

    def _execute_method(self):
        """
        Dynamically imports and runs the appropriate module function.
        """
        method = self.conf['method']
        self.logger.debug(f"Executing method: {method}")

        try:
            if method == 'stage1':
                from ispider_core.crawlers.stage1 import _stage1_crawl_bot
                _stage1_crawl_bot(self.manager, self.shared_counter, self.conf)

            elif method == 'spider-st2':
                from ispider_core.modules._st2_spider_bot import _spider_bot
                _spider_bot(self.manager, self.shared_counter, self.conf)

            elif method.startswith('parse'):
                self._execute_parse_method(method)

            else:
                self.logger.error(f"Unknown method: {method}")
                raise ValueError(f"Unknown method: {method}")

        except Exception as e:
            self.logger.exception(f"Error executing method {method}: {str(e)}")

    def _execute_parse_method(self, method):
        """
        Handles parsing-related tasks based on the METHOD.
        """
        parse_stage1 = ['parse-conn-landings', 'parse-conn-robots', 'parse-conn-sitemaps']
        parse_stage2 = ['parse-conn-internals', 'parse-jsons', 'parse-urls-ext', 'parse-emails', 'parse-keywords']

        try:
            if method in parse_stage1:
                from ispider_core.modules._st1_parse_conn import _parse_conn
                _parse_conn(self.manager, self.shared_counter, self.conf)

            elif method in parse_stage2:
                from ispider_core.modules._st2_parse import _st2_parse
                _st2_parse(self.manager, self.shared_counter, self.conf)

            elif method == 'parse-sitemaps':
                from ispider_core.modules._st1_parse import _st1_parse
                _st1_parse(self.manager, self.shared_counter, self.conf)

            else:
                self.logger.error(f"Unknown parsing method: {method}")
                raise ValueError(f"Unknown parsing method: {method}")

        except Exception as e:
            self.logger.exception(f"Error in parsing method {method}: {str(e)}")
