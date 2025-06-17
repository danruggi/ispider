from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import multiprocessing
import os
from pathlib import Path
import json
import time
import threading
import sys
import uvicorn
import signal
import asyncio

import contextlib
from datetime import datetime
from contextlib import asynccontextmanager

from ispider_core.ispider import ISpider
from ispider_core.config import Settings
from ispider_core.utils.logger import LoggerFactory


from pathlib import Path

# Create a logs directory inside /tmp or wherever is appropriate
log_dir = Path("/tmp/ispider_logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Use timestamped log file
log_file_path = log_dir / f"ispider.log"
log_file = open(log_file_path, "a")

# Redirect stdout and stderr to file
sys.stdout = log_file
sys.stderr = log_file

print(f"[LOGGING] Redirected output to: {log_file_path}")




## GLOBAL VARIABLES
spider_instance = None
spider_config = None
spider_status = None
start_time = None
global_server = None
shutdown_event = threading.Event()

# CLASSES
class Server(uvicorn.Server):
    
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                print("STARTING")
                time.sleep(1e-3)
            yield
            print("STARTED")
        finally:
            self.should_exit = True
            thread.join()

    def run(self, sockets=None):
        print("[Server.run] Starting run()")
        def wrapper():
            self.started = True
            print("[Server.run] Marked started = True")
            return self.serve(sockets=sockets)

        return asyncio.run(wrapper())

    def shutdown_server(self):
        """Directly shut down server instance and its loop"""
        self.should_exit = True
        self.force_exit = True  # <- ADD THIS
        print("[Server -> shutdown] Shutting down")
        if hasattr(self, 'server') and self.server is not None:
            self.server.should_exit = True
            self.server.force_exit = True
            if hasattr(self.server, 'loop') and self.server.loop is not None:
                self.server.loop.call_soon_threadsafe(self.server.loop.stop)  # <- force asyncio loop to break

    def run_and_wait(self):
        """Start server in thread, wait for shutdown_event, then clean up."""
        with self.run_in_thread():
            print("[main] Server started")
            try:
                shutdown_event.wait()
            except KeyboardInterrupt:
                print("Keyboard interrupt received")
            finally:
                try:
                    print("Shutting down server…")
                    close_spider()
                    self.shutdown_server()
                except Exception as e:
                    print(f"Possibly not a clen shutdown {e}")
        print("Server fully shut down")



class SpiderConfig(BaseModel):
    domains: List[str] = []
    stage: Optional[str] = None
    user_folder: str = "~/.ispider/"
    log_level: str = "DEBUG"
    pools: int = 4
    async_block_size: int = 4
    maximum_retries: int = 2
    codes_to_retry: List[int] = [430, 503, 500, 429]
    engines: List[str] = ["httpx", "curl"]
    crawl_methods: List[str] = ["robots", "sitemaps"]
    max_pages_per_domain: int = 5000
    websites_max_depth: int = 5
    sitemaps_max_depth: int = 2
    timeout: int = 5

class DomainAddRequest(BaseModel):
    domains: List[str]


## LIFESPAN
@asynccontextmanager
async def lifespan(app: FastAPI):
    global spider_instance, spider_config, spider_status, start_time
    
    # UI watchdog setup
    try:
        if ui_pid_str := os.getenv("ISP_UI_PID"):
            try:
                ui_pid = int(ui_pid_str)
                print(f"[lifespan] 👀 Watching UI PID: {ui_pid}")
                # Non-daemon thread for reliable cleanup
                threading.Thread(
                    target=ui_watchdog, 
                    args=(ui_pid,),
                    daemon=False
                ).start()
            except ValueError:
                print("Invalid ISP_UI_PID format")
                
        # Spider initialization
        config = SpiderConfig(
            domains=[],
            stage="unified",
            user_folder="/Volumes/Sandisk2TB/test_business_scraper_22"
        )

        spider_config = config
        spider_instance = ISpider(domains=config.domains, stage=config.stage, **config.model_dump(exclude={"domains", "stage"}))
        spider_status = "initialized"
        start_time = time.time()
        
        threading.Thread(target=run_spider, daemon=True).start()

        yield

    except asyncio.CancelledError:
        print("[lifespan] ⚠️ Cancelled -- Error during shutdown — safe to ignore")
    finally:
        close_spider()
        if not shutdown_event.is_set():
            shutdown_event.set()



app = FastAPI(
    title="ISpider API", 
    description="API for controlling the ISpider web crawler",
    version="0.1.0",
    lifespan=lifespan
)
# CORS configuration

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def ui_watchdog(ui_pid):
    """Watchdog that triggers shutdown event on UI death"""
    while not shutdown_event.is_set():
        try:
            os.kill(ui_pid, 0)  # Check process existence
            # print(f"[Wathcdog] running, {shutdown_event.is_set()}")
            # time.sleep(10)
            # raise Exception("Kill")
        except Exception as e:
            print(f"[Wathcdog] 🚨 UI PID {ui_pid} died → API shutdown: {e}")
            shutdown_event.set()  # Signal main thread
            break
        time.sleep(1)




def close_spider():
    global spider_instance
    if spider_instance:
        try:
            print("Shutting down spider...")
            spider_instance.shutdown()
        except Exception as e:
            print(f"Shutdown error: {str(e)}")
        finally:
            spider_instance = None

def run_spider():
    global spider_instance, spider_status
    try:
        spider_status = "running"
        spider_instance._ensure_manager()
        spider_instance.run()
        spider_status = "completed"
    except Exception as e:
        spider_status = "failed"
        print(f"[ERROR] Spider failed: {e}")


### FASTAPI METHODS
@app.post("/spider/domains/add")
async def add_domains(request: DomainAddRequest):
    global spider_instance  # assuming you have a single global spider instance

    if not spider_instance:
        raise HTTPException(status_code=500, detail="Spider not initialized")

    new_domains = request.domains
    shared_new_domains = spider_instance.shared_new_domains

    if shared_new_domains is None:
        raise HTTPException(status_code=500, detail="Spider does not support dynamic domain addition")

    shared_new_domains.extend(new_domains)

    return {"message": "Domains added successfully", "added_domains": new_domains}


@app.get("/spider/domains")
async def get_domains():
    global spider_instance
    if not spider_instance or not spider_instance.shared_dom_stats:
        return {"domains": []}
    
    dom_stats = spider_instance.shared_dom_stats
    domains = list(dom_stats.dom_missing.keys())  # Correctly get domain list
    return {"domains": domains}


@app.get("/spider/status")
async def get_status():
    global spider_instance

    dom_stats = spider_instance.shared_dom_stats
    if dom_stats is None:
        raise HTTPException(status_code=500, detail="Domain stats not available")

    running_time = time.time() - start_time if start_time else 0

    status = {'script_controller': spider_instance.shared_script_controller}

    with dom_stats.lock:
        status['domains'] = {}
        for dom in dom_stats.dom_missing.keys():
            try:
                progress = round(((dom_stats.dom_total[dom]-dom_stats.dom_missing[dom])/dom_stats.dom_total[dom]), 2)
            except:
                progress = 0

            status['domains'][dom] = {
                "domain": dom,
                "status": "Finished" if dom_stats.dom_missing[dom] == 0 else "Running",
                "progress": progress,
                "speed": 0,
                "pagesFound": dom_stats.dom_total[dom],
                "hasRobot": dom_stats.local_stats[dom].get('has_robot', False),
                "hasSitemaps": dom_stats.local_stats[dom].get('has_sitemaps', False),
                "bytes": dom_stats.local_stats[dom].get('bytes', 0),
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "missing": dom_stats.dom_missing[dom],
                "total": dom_stats.dom_total[dom],
                "last_call": dom_stats.dom_last_call.get(dom, 0),
                "engine": dom_stats.dom_engine.get(dom)
            }

    return status


@app.get("/spider/config/get", response_model=SpiderConfig)
async def get_config():
    global spider_config
    if not spider_config:
        raise HTTPException(status_code=404, detail="No configuration set")
    
    return spider_config.model_dump(exclude={"domains", "stage"})


@app.post("/spider/config/set")
async def set_config(new_config: SpiderConfig):
    global spider_instance, spider_config, spider_status, start_time

    # Stop current spider
    close_spider()

    # Save and apply new config
    spider_config = new_config
    spider_instance = ISpider(
        domains=new_config.domains,
        stage=new_config.stage,
        **new_config.model_dump(exclude={"domains", "stage"})
    )
    spider_status = "initialized"
    start_time = time.time()

    # Start the new spider in a thread
    threading.Thread(target=run_spider, daemon=True).start()

    return {"message": "Spider restarted with new config", "config": new_config.model_dump()}

@app.get("/spider/stop")
async def stop_spider():
    close_spider()
    return {"message": "Stop signal sent"}


if __name__ == "__main__":
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=5,
        access_log=False
    )
    server = Server(config)

    with server.run_in_thread():
        print("[main] Server started")
        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            print("Keyboard interrupt received")
        finally:
            print("Shutting down server…")
            close_spider()
            server.shutdown_server()

    print("Server fully shut down")
