from ispider_core.utils.logger import LoggerFactory
from ispider_core.crawlers import cls_controllers

import time

class Orchestrator:
    def __init__(self, conf, manager, shared_counter):
        self.controller = None
        self.conf = conf
        self.manager = manager
        self.shared_counter = shared_counter
        self.logger = LoggerFactory.create_logger("./logs", "orchestrator.log", log_level=conf['LOG_LEVEL'], stdout_flag=True)

    @property
    def shared_new_domains(self):
        self.logger.info("Orchestrator, adding domains")
        if self.controller:
            attrs = dir(self.controller)
            self.logger.info(f"Controller attributes: {attrs}")
            if hasattr(self.controller, 'shared_new_domains'):
                return self.controller.shared_new_domains
        self.logger.info("Controller is none")
        return None

    @property
    def shared_fetch_controller(self):
        if self.controller and hasattr(self.controller, 'shared_fetch_controller'):
            return self.controller.shared_fetch_controller
        return None

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
            if method == 'crawl':
                self.controller = cls_controllers.CrawlController(self.manager, self.conf, self.shared_counter)
                self.controller.run()
            elif method == 'spider':
                self.controller = cls_controllers.SpiderController(self.manager, self.conf, self.shared_counter)
                self.controller.run()
            elif method == 'unified':
                self.controller = cls_controllers.UnifiedController(self.manager, self.conf, self.shared_counter)
                self.controller.run()
            else:
                self.logger.error(f"Unknown stage method: {method}")
                raise ValueError(f"Unknown stage method: {method}")
        except Exception as e:
            self.logger.exception(f"Error executing {method}: {e}")

    def shutdown(self):
        self.manager.shutdown()