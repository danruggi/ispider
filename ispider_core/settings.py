## *********************************
## GENERIC SETTINGS
# Output folder for controllers, dumps, and JSONs
USER_FOLDER = "~/.ispider/"

# Logging level
LOG_LEVEL = 'DEBUG'

# Retry for specific status codes
# e.g., status_code = 430
CODES_TO_RETRY = [430, 503, 500, 429]
MAXIMUM_RETRIES = 2

# Delay time (in seconds) before retrying after a failed status code
TIME_DELAY_RETRY = 0

# Number of concurrent connections per process during crawling
ASYNC_BLOCK_SIZE = 4

# Number of parallel processes (based on your CPU core count)
POOLS = 4

# Maximum timeout for each connection (in seconds)
TIMEOUT = 5

# This must be a list.
# curl is used as a subprocess, so make sure it is installed on your system.
# Retry logic will try the next engine in the list.
# The script starts with the ultra-fast httpx.
# If it fails, it tries curl.
# If that fails, it tries seleniumbase in headless mode with UC activated.
ENGINES = ['httpx', 'curl', 'seleniumbase']

# Use --insecure with curl if True
CURL_INSECURE = False

## *********************************
# CRAWLER
# Maximum file size (in bytes) allowed for dumps.
# This helps avoid saving large sitemaps with errors.
MAX_CRAWL_DUMP_SIZE = 52428800

# Maximum depth to follow in sitemaps
SITEMAPS_MAX_DEPTH = 2

# Methods used during crawl phase
CRAWL_METHODS = ['robots', 'sitemaps']

## *********************************
## SPIDER
# Maximum queue size; 1 billion is acceptable on most systems
QUEUE_MAX_SIZE = 100000

# Maximum depth to follow when crawling websites
WEBSITES_MAX_DEPTH = 2

# This feature is implemented but not yet thread-safe.
# While counting, other workers might add links that aren't included in the count,
# which can result in more pages being downloaded per domain than expected.
# Adding this check under a lock could slow things down and needs further testing.
MAX_PAGES_POR_DOMAIN = 5000

# Attempt to exclude certain file types.
# Also inspects the first bytes of content for commonly excluded file types,
# even if the URL doesn't have a typical file extension.
EXCLUDED_EXTENSIONS = [
    "pdf", "csv",
    "mp3", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg", "ico", "tif",
    "jfif", "eps", "raw", "cr2", "nef", "orf", "arw", "rw2", "sr2", "dng", "heif", "avif", "jp2", "jpx",
    "wdp", "hdp", "psd", "ai", "cdr", "ppsx",
    "ics", "ogv",
    "mpg", "mp4", "mov", "m4v",
    "zip", "rar"
]

# Exclude any URL that matches one of these regex patterns
EXCLUDED_EXPRESSIONS_URL = [
    # r'test',
]