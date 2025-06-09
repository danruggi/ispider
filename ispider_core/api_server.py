# api.py
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

from ispider_core.ispider import ISpider
from ispider_core.config import Settings
from ispider_core.utils.logger import LoggerFactory

app = FastAPI(title="ISpider API", 
              description="API for controlling the ISpider web crawler",
              version="0.1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global state for active spiders
spider_instance = None
spider_config = None
spider_status = "not_started"
start_time = None

class SpiderConfig(BaseModel):
    domains: List[str] = []
    stage: Optional[str] = None
    user_folder: str = "/Volumes/Sandisk2TB/test_business_scraper_22"
    log_level: str = "DEBUG"
    pools: int = 4
    async_block_size: int = 4
    maximum_retries: int = 2
    codes_to_retry: List[int] = [430, 503, 500, 429]
    engines: List[str] = ["httpx", "curl"]
    crawl_methods: List[str] = ["robots", "sitemaps"]
    max_pages_per_domain: int = 5000
    websites_max_depth: int = 2
    sitemaps_max_depth: int = 2
    timeout: int = 5

class DomainAddRequest(BaseModel):
    domains: List[str]

class SpiderStatusResponse(BaseModel):
    spider_id: str
    status: str
    config: Dict[str, Any]
    stats: Dict[str, Any]
    fetch_controller: Dict[str, int]
    queue_size: int
    processed_count: int


@app.on_event("startup")
async def start_unified_spider():
    global spider_instance, spider_config, spider_status, start_time

    config = SpiderConfig(
        domains=[],
        stage="unified",
        user_folder="/Volumes/Sandisk2TB/test_business_scraper_22"
    )
    spider_config = config
    spider_instance = ISpider(domains=config.domains, stage=config.stage, **config.dict(exclude={"domains", "stage"}))
    spider_status = "initialized"
    start_time = time.time()

    def run_in_background():
        run_spider()

    threading.Thread(target=run_in_background, daemon=True).start()

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



@app.get("/spider/status")
async def get_status():
    global spider_instance, spider_status, start_time, spider_config

    running_time = time.time() - start_time if start_time else 0
    return {
        "status": spider_status,
        "running_time": running_time,
        "config": spider_config.dict() if spider_config else {},
        "processed_count": spider_instance.shared_counter.value if spider_instance and hasattr(spider_instance, 'shared_counter') else 0
    }



@app.post("/spider/stop")
async def stop_spider():
    global spider_status
    spider_status = "stopping"
    return {"message": "Stop signal sent (graceful shutdown not yet implemented)"}


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)