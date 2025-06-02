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


