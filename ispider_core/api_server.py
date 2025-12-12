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


""" Redirect all to /tmp/spider_log """
log_dir = Path("/tmp/ispider_logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file_path = log_dir / f"ispider.log"
log_file = open(log_file_path, "a")
sys.stdout = log_file
sys.stderr = log_file
# print(f"[LOGGING] Redirected output to: {log_file_path}")


## GLOBAL VARIABLES
spider_instance = None
spider_config = None
spider_status = None
start_time = None
global_server = None
shutdown_event = threading.Event()


## LIFESPAN, must be first. 
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
        
        sc = app.state.spider_config
        print(f"[lifespan] config: {sc}")
        

        # # Spider initialization
        # config = SpiderConfig(
        #     domains=[],
        #     stage="unified",
        # )

        # if isp_out_folder := os.getenv("ISP_OUT_FOLDER"):
        #     config.user_folder = isp_out_folder

        # spider_config = config
        spider_instance = ISpider(domains=sc.domains, stage=sc.stage, **sc.model_dump(exclude={"domains", "stage"}))
        spider_status = "initialized"
        start_time = time.time()
        
        threading.Thread(target=run_spider, daemon=True).start()

        yield
        print("[lifespan] Finished")


    except asyncio.CancelledError:
        # We can't avoid this error. It's part of uvicorn/starlette/asyncio
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

class SpiderConfig(BaseModel):
    domains: List[str] = []
    stage: Optional[str] = None
    user_folder: str = os.path.expanduser("~/.ispider/")
    log_level: str = "DEBUG"
    pools: int = 2
    async_block_size: int = 2
    maximum_retries: int = 2
    codes_to_retry: List[int] = [430, 503, 500, 429]
    engines: List[str] = ["httpx", "curl"]
    crawl_methods: List[str] = ["robots", "sitemaps"]
    max_pages_per_domain: int = 5000
    websites_max_depth: int = 5
    sitemaps_max_depth: int = 2
    timeout: int = 5
    resume: bool = False

class DomainAddRequest(BaseModel):
    domains: List[str]

class Server(uvicorn.Server):
    def __init__(self, config, spider_config: Optional[SpiderConfig] = None):
        super().__init__(config)
        self._started_evt = threading.Event()
        self.spider_config = spider_config or SpiderConfig()
        app.state.spider_config = self.spider_config

    @contextlib.contextmanager
    def run_in_thread(self):
        # Start server thread
        thread = threading.Thread(target=self._run_wrapper, daemon=True)
        thread.start()
        # Block until server loop actually starts
        self._started_evt.wait()
        try:
            yield
        finally:
            # Signal shutdown and wait for thread
            self.should_exit = True
            thread.join()

    def _run_wrapper(self):
        # Mark started before entering serve
        self._started_evt.set()
        super().run()

    def run_and_wait(self):
        with self.run_in_thread():
            print("[run_and_wait] Server started")
            try:
                shutdown_event.wait()
            except KeyboardInterrupt:
                print("[run_and_wait] Keyboard interrupt received")
            finally:
                print("[run_and_wait] Shutting down server…")
                close_spider()


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


@app.get("/spider/domains/list")
async def get_domains_list():
    global spider_instance
    if not spider_instance or not spider_instance.shared_dom_stats:
        return {"domains": []}
    
    dom_stats = spider_instance.shared_dom_stats
    domains = list(dom_stats.dom_missing.keys())  # Correctly get domain list
    return {"domains": domains}


@app.get("/spider/domains")
async def get_domains():
    global spider_instance
    dom_stats = spider_instance.shared_dom_stats
    if dom_stats is None:
        raise HTTPException(status_code=500, detail="Domain stats not available")

    status = {}
    with dom_stats.lock:
        for dom in dom_stats.dom_missing.keys():
            missing_pages = dom_stats.dom_missing[dom]
            total_pages = dom_stats.dom_total[dom]
            try:
                progress = round(((dom_stats.dom_total[dom]-dom_stats.dom_missing[dom])/dom_stats.dom_total[dom]), 2)
            except:
                progress = 0

            status[dom] = {
                "domain": dom,
                "status": "Finished" if dom_stats.dom_missing[dom] == 0 else "Running",
                "progress": progress,
                "speed": 0,
                "pagesFound": dom_stats.dom_total[dom],
                "pagesDownloaded": dom_stats.dom_total[dom] - dom_stats.dom_missing[dom],
                "hasRobot": dom_stats.local_stats[dom].get('has_robot', False),
                "hasSitemaps": dom_stats.local_stats[dom].get('has_sitemaps', False),
                
                "lastCall": dom_stats.dom_last_call.get(dom).isoformat(timespec='seconds') + "Z" if dom_stats.dom_last_call.get(dom) else None,
                "lastStatus": dom_stats.local_stats.get(dom, 0).get('last_status_code', 0),
                
                "bytes": dom_stats.local_stats[dom].get('bytes', 0),
                "missing": dom_stats.dom_missing[dom],
                "total": dom_stats.dom_total[dom],
                "engine": dom_stats.dom_engine.get(dom),
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
    

@app.get("/spider/status")
async def spider_status():
    global spider_instance, spider_status
    if spider_status == "running" and spider_instance:
        return {"running": True}    

    raise HTTPException(status_code=503, detail="Spider not running")


if __name__ == "__main__":
    ''' 
    Not used for the actual process, 
    everything is called in Server -> run_and_wait
    This is just for direct call 
    python api_server.py
    '''
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=5,
        access_log=True
    )
    server = Server(config)

    with server.run_in_thread():
        print("[main] Server started")
        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            print("[main] Keyboard interrupt received")
        finally:
            print("[main] Shutting down server…")
            close_spider()
            if not shutdown_event.is_set():
                shutdown_event.set()

    print("[main] Server fully shut down")
