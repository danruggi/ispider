# ispider_core

# V0.1

**ispider** is a module to spider websites

- multi - queue system
- multicore and multithreads, 
- accept hundreds/thousands of websites/domains as input
- sparse connections to avoid repeated requests against the same domain


It was designed to get the maximum speed, so it has some limitations;
- as v 0.2, it does not support files (pdf, video, images, etc), it gets just html


# USAGE
pip install ispider

```
  from ispider_core import ISpider

  doms = ["https://www.example1.com/", "https://www.example2.com/"]
  ISpider(domains=doms, stage="crawl").run()
  ISpider(domains=doms, stage="spider").run()
```

# TO KNOW
At first execution, 
- It creates the folder ~/.ispider
- It downloads the file

https://raw.githubusercontent.com/danruggi/ispider/dev/static/exclude_domains.csv

that's a list of almost-infinite domains that would retain the script forever
(or other domains too that were not needed in my project)
You can update the file in ~/.ispider/sources


# SETTINGS
Actual settings are:

CODES_TO_RETRY = [430, 503, 500, 429] 
MAXIMUM_RETRIES = 2
TIME_DELAY_RETRY = 0

QUEUE_MAX_SIZE = 100000

ASYNC_BLOCK_SIZE = 4
POOLS = 4
TIMEOUT = 5

MAX_CRAWL_DUMP_SIZE = 52428800

SITEMAPS_MAX_DEPTH = 10 //not implementesd
WEBSITES_MAX_DEPTH = 2 // not implemented
MAX_PAGES_POR_DOMAIN = 1000000

EXCLUDED_EXTENSIONS = [
    "pdf", "csv",
    "mp3", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg", "ico", "tif",
    "jfif", "eps", "raw", "cr2", "nef", "orf", "arw", "rw2", "sr2", "dng", "heif", "avif", "jp2", "jpx",
    "wdp", "hdp", "psd", "ai", "cdr", "ppsx"
    "ics", "ogv",
    "mpg", "mp4", "mov", "m4v",
    "zip", "rar"
]

EXCLUDED_EXPRESSIONS_URL = [
    r'test',
]

USER_FOLDER = "~/.ispider/"

LOG_LEVEL = 'DEBUG'

CRAWL_METHODS = ['robots', 'sitemaps']
ENGINE = ['httpx', 'curl']