from ispider_core.utils.logger import LoggerFactory
from ispider_core.crawlers import cls_controllers

import time

class Orchestrator:
    def __init__(self, conf, manager, shared_counter):
        self.conf = conf
        self.manager = manager
        self.shared_counter = shared_counter
        self.logger = LoggerFactory.create_logger("./logs", "orchestrator.log", log_level=conf['LOG_LEVEL'], stdout_flag=True)

    def run(self):
        start_time = time.time()
        self.logger.info(f"*** BEGIN METHOD {self.conf['method']} ***")
        self._execute_method()
        duration = round(time.time() - start_time, 2)
        avg_speed = round(self.shared_counter.value / duration, 2) if duration > 0 else 0
        self.logger.info(f"*** ENDS {self.conf['method']} - {self.shared_counter.value} items in {duration}s; {avg_speed} items/s ***")

    def _execute_method(self):
        method = self.conf['method']
        self.logger.debug(f"Executing: {method}")
        try:
            if method in ['crawl']:
                cls_controllers.CrawlController(self.manager, self.conf, self.shared_counter).run()
            elif method in ['spider']:
                cls_controllers.SpiderController(self.manager, self.conf, self.shared_counter).run()

            else:
                self.logger.error(f"Unknown stage method: {method}")
                raise ValueError(f"Unknown stage method: {method}")
        except Exception as e:
            self.logger.exception(f"Error executing {method}: {e}")
