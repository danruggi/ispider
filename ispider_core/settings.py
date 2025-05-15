## i.e., status_code = 430
CODES_TO_RETRY = [430, 503, 500, 429]
MAXIMUM_RETRIES = 2
TIME_DELAY_RETRY = 0

QUEUE_MAX_SIZE = 100000

## Number of concurrent connection on the same process during crawling
ASYNC_BLOCK_SIZE = 2
POOLS = 2
TIMEOUT = 5

# Number of cores to be used

ROBOTS = False
SITEMAPS = False

# FILE SIZES 
## Max file size dumped on the disk. Avoid big sitemaps with errors
MAX_CRAWL_DUMP_SIZE = 52428800

SITEMAPS_MAX_DEPTH = 10
WEBSITES_MAX_DEPTH = 20
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

USER_FOLDER = "~/.ispider/"

LOG_LEVEL = 'DEBUG'
