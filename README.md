# ispider_core

# V0.2

**ispider** is a module to spider websites

- Multicore and multithreaded  
- Accepts hundreds/thousands of websites/domains as input  
- Sparse connections to avoid repeated requests against the same domain  
- The `httpx` engine works in asyncio blocks defined by `settings.ASYNC_BLOCK_SIZE`, so total concurrent threads are `ASYNC_BLOCK_SIZE * POOLS`

It was designed for maximum speed, so it has some limitations:  
- As of v0.2, it does not support files (pdf, video, images, etc); it only processes HTML


# HOW IT WORKS - SIMPLE
**-- Crawl - Depth == 0**  
- Get all the landing pages for domains in the provided list.  
- If "robots" is selected, download the `robots.txt` file.  
- If "sitemaps" is selected, parse the `robots.txt` and retrieve all the sitemaps.  
- All data is saved under `USER_DATA/data/dumps/dom_tld`.

**-- Spider - Depth > 0**  
- Extract all links from landing pages and sitemaps.  
- Download the HTML pages, extract internal links, and follow them recursively.

# HOW IT WORKS - MORE DETAILED

#### Crawl - Depth == 0
- Create objects in the form (`('https://domain.com', 'landing_page', 'domain.com', depth, retries, engine)`)  
- Add them to the LIFO queue `qout`  
- A thread retrieves elements from `qout` in variable-size blocks (depending on `QUEUE_MAX_SIZE`)  
- Fill a FIFO queue `qin`  
- Different workers (defined in `settings.POOLS`) get elements from `qin` and download them to `USER_DATA/data/dumps/dom_tld`  
- Landing pages are saved as `_.html`  
- Each worker processes the landing page; if the result is OK (`status_code == 200`), it tries to get `robots.txt`  
- On failure, it tries the next available engine (fallback)  
- It creates an object (`('https://domain.com/robots.txt', 'robots', 'domain.com', depth=1, retries=0, engine)`)  
- Each worker retrieves the `robots.txt`; if `"sitemaps"` is defined in `settings.CRAWL_METHODS`, it attempts to get all sitemaps from `robots.txt` and `dom_tld/sitemaps.xml`  
- It creates objects (`('https://domain.com/sitemap.xml', 'sitemaps', 'domain.com', depth=1, retries=0, engine)`) and for other sitemaps found in `robots.txt`  
- Every successful or failed download is logged as a row in `USER_FOLDER/jsons/crawl_conn_meta*json` with all information available from the engine; these files are useful for statistics/reports from the spider  
- When there are no more elements in `qin`, after a 90-second timeout, jobs stop.

#### Spider - Depths > 0
- It reads entries from `USER_FOLDER/jsons/crawl_conn_meta*json` for the domains in the list  
- It retrieves landing pages and sitemaps  
- If sitemaps are compressed, it uncompresses them  
- Extract all links from landing pages and sitemaps  
- Create objects (`('https://domain.com/link1', 'internals', 'domain.com', depth=2, retries=0, engine)`)  
- Use the same engine that was used for the last successful request to the domain TLD  
- Add these objects to `qout`  
- Thread `qin` moves blocks from `qout` to `qin`, sparsing them  
- Download all links, save them, and save data in JSON  
- Parse the HTML, extract all INTERNAL links, follow them recursively, increasing depth  

#### Schema
This is the projectual schema of the crawler/spider
![alt text](https://imgur.com/a/cQUqf3O)

# USAGE

Install it
```
pip install ispider
```

First use
```
from ispider_core import ISpider
import pandas as pd

if __name__ == '__main__':
    config_overrides = {
        'USER_FOLDER': '/Your/Dump/Folder',
        'POOLS': 64,
        'ASYNC_BLOCK_SIZE': 32,
        'MAXIMUM_RETRIES': 2,
        'CRAWL_METHODS': [],
        'CODES_TO_RETRY': [430, 503, 500, 429, -1],
        'CURL_INSECURE': True,
        'ENGINES': ['curl']
    }

    # Load a file with domains, convert it to a list
    # doms = ['domain1.com', 'domain2.com'....]
    df = pd.read_csv('t.csv')
    doms = df['dom_tld'].tolist()

    # Begin to run
    # Crawl takes landings, robots, sitemaps
    ISpider(domains=doms, stage="crawl", **config_overrides).run()
    # Spider get all links from Crawled pages
    ISpider(domains=doms, stage="spider", **config_overrides).run()
```

# TO KNOW
At first execution, 
- It creates the folder settings.USER_FOLDER
- It downloads the file in settings.USER_FOLDER/sources/

https://raw.githubusercontent.com/danruggi/ispider/dev/static/exclude_domains.csv

that's a list of almost-infinite domains that would retain the script forever
(or other domains too that were not needed in my project)
You can update the file in ~/.ispider/sources

- It creates settings.USER_FOLDER/data/ with dumps/ and jsons/
- dumps are the downloaded websites
- jsons are the connection results for every request


# SETTINGS
Actual default settings are:

        """
        ## *********************************
        ## GENERIC SETTINGS
        # Output folder for controllers, dumps and jsons
        USER_FOLDER = "~/.ispider/"

        # Log level
        LOG_LEVEL = 'DEBUG'

        ## i.e., status_code = 430
        CODES_TO_RETRY = [430, 503, 500, 429]
        MAXIMUM_RETRIES = 2

        # Delay time after some status code to be retried
        TIME_DELAY_RETRY = 0

        ## Number of concurrent connection on the same process during crawling
        # Concurrent por process
        ASYNC_BLOCK_SIZE = 4

        # Concurrent processes (number of cores used, check your CPU spec)
        POOLS = 4

        # Max timeout for connecting,
        TIMEOUT = 5

        # This need to be a list, 
        # curl is used as subprocess, so be sure you installed it on your system
        # Retry will use next available engine.
        # The script begins wit the suprfast httpx
        # If fail, try with curl
        # If fail, it tries with seleniumbase, headless and uc mode activate
        ENGINES = ['httpx', 'curl', 'seleniumbase']

        CURL_INSECURE = False

        ## *********************************
        # CRAWLER
        # File size 
        # Max file size dumped on the disk. 
        # This to avoid big sitemaps with errors.
        MAX_CRAWL_DUMP_SIZE = 52428800

        # Max depth to follow in sitemaps
        SITEMAPS_MAX_DEPTH = 2

        # Crawler will get robots and sitemaps too
        CRAWL_METHODS = ['robots', 'sitemaps']

        ## *********************************
        ## SPIDER
        # Queue max, till 1 billion is ok on normal systems
        QUEUE_MAX_SIZE = 100000

        # Max depth to follow in websites
        WEBSITES_MAX_DEPTH = 2

        # This is not implemented yet
        MAX_PAGES_POR_DOMAIN = 1000000

        # This try to exclude some kind of files
        # It also test first bits of content of some common files, 
        # to exclude them even if online element has no extension
        EXCLUDED_EXTENSIONS = [
            "pdf", "csv",
            "mp3", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg", "ico", "tif",
            "jfif", "eps", "raw", "cr2", "nef", "orf", "arw", "rw2", "sr2", "dng", "heif", "avif", "jp2", "jpx",
            "wdp", "hdp", "psd", "ai", "cdr", "ppsx"
            "ics", "ogv",
            "mpg", "mp4", "mov", "m4v",
            "zip", "rar"
        ]

        # Exclude all urls that contains this REGEX
        EXCLUDED_EXPRESSIONS_URL = [
            # r'test',
        ]

        """


# NOTES
- Deduplication is not 100% safe, sometimes pages are downloaded multiple times, and skipped in file check. On ~10 domains, this create small delay. But on 10000 domains after 500k links, the domain list is so big that checking if a link is already downloaded or not was decreasing considerably the speed (from 30000 urls/min to 300 urls/min).