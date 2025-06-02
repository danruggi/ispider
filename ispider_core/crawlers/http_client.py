from datetime import datetime
import asyncio
import functools

import httpx

from ispider_core.engines import mod_httpx
from ispider_core.engines import mod_curl
from ispider_core.engines import mod_seleniumbase

import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor


async def handle_httpx(reqsA, conf, mod=0, headers={}):
    timeout = httpx.Timeout(30, connect=conf['TIMEOUT'])
    limits = httpx.Limits(max_connections=100)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, headers=headers) as client:
        tasks = [
            mod_httpx.fetch_with_httpx(reqA, client, mod)
            for reqA in reqsA
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

def handle_curl(reqsA, conf, mod=0):
    with ThreadPoolExecutor() as executor:
        tasks = [
            executor.submit(mod_curl.fetch_with_curl, reqA, conf)
            for reqA in reqsA
        ]
        return [t.result() for t in tasks]

def handle_seleniumbase(reqsA, lock_driver, conf, mod=0):
    with ThreadPoolExecutor(max_workers=1) as executor:
        tasks = [
            executor.submit(mod_seleniumbase.fetch_with_seleniumbase, reqA, lock_driver, mod, conf)
            for reqA in reqsA
        ]
        return [t.result() for t in tasks]


def fetch_all(reqsA, lock_driver, conf, mod=0, headers={}):
    httpx_reqs = [r for r in reqsA if r[5] == "httpx"]
    curl_reqs = [r for r in reqsA if r[5] == "curl"]
    seleniumbase_reqs = [r for r in reqsA if r[5] == "seleniumbase"]

    results = []

    if httpx_reqs:
        httpx_results = asyncio.run(handle_httpx(httpx_reqs, conf, mod, headers))
        results.extend(httpx_results)

    if curl_reqs:
        curl_results = handle_curl(curl_reqs, conf, mod)
        results.extend(curl_results)

    if seleniumbase_reqs:
        seleniumbase_results = handle_seleniumbase(seleniumbase_reqs, lock_driver, conf, mod)
        results.extend(seleniumbase_results)
        
    return results