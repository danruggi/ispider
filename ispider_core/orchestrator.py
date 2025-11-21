from ispider_core.utils.logger import LoggerFactory
from ispider_core.crawlers import cls_controllers

import time

class Orchestrator:
    def __init__(self, conf, manager):
        self.controller = None
        self.conf = conf
        self.manager = manager
        self.logger = LoggerFactory.create_logger(self.conf, "ispider.log", stdout_flag=True)

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
    def shared_dom_stats(self):
        if self.controller and hasattr(self.controller, 'shared_dom_stats'):
            return self.controller.shared_dom_stats
        return None

    @property
    def shared_script_controller(self):
        if self.controller and hasattr(self.controller, 'shared_script_controller'):
            return self.controller.shared_script_controller
        return None

    def run(self):
        start_time = time.time()
        self.logger.info(f"*** BEGIN METHOD Unified ***")

        try:
            self.logger.debug(f"Executing: Unified")
            
            # Launch the main controller
            self.controller = cls_controllers.UnifiedController(self.manager, self.conf)
            self.controller.run()

        except Exception as e:
            self.logger.exception(f"Error executing unified: {e}")

        duration = round(time.time() - start_time, 2)
        self.logger.info(f"*** ENDS Unified - Exec time {duration}s")


    def shutdown(self):
        
        if self.controller and hasattr(self.controller, "_shutdown"):
            self.controller._shutdown()

