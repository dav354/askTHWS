# Scrapy settings for thws_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# ##################################################
# Custom values; might be configureable via env tbd
# ##################################################

# Size of the chunks
CHUNK_SIZE = 1000

# Overlapping of the chunks
CHUNK_OVERLAP = 100

ENABLE_FILE_LOGGING = True

EXPORT_CSV_STATS = True

# ##################################################

# Identifier for your bot. Used in logs, the default User-Agent header, etc.
BOT_NAME = "thws_scraper"

# Where Scrapy will look for your Spider classes
SPIDER_MODULES = ["thws_scraper.spiders"]
NEWSPIDER_MODULE = "thws_scraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "thws-scraper-bot/0.3.3"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 0.5
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "thws_scraper.middlewares.ThwsScraperSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # default priority is 550
    "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": None,  # disable the built-in # noqa: E501
    "thws_scraper.middlewares.RobotsBypassMiddleware": 100,  # Enable the custom one
    "thws_scraper.middlewares.ThwsErrorMiddleware": 550,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html

ITEM_PIPELINES = {
    # JSON Ouptut
    "thws_scraper.pipelines.RawOutputPipeline": 100,  # write raw pages first
    "thws_scraper.pipelines.ChunkingOutputPipeline": 200,  # then split & emit chunks
    # Postgres Output
    "thws_scraper.pipelines.RawPostgresPipeline": 100,  # write raw pages first
    "thws_scraper.pipelines.ChunkingPostgresPipeline": 200,  # then split & emit chunks
}


# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings # noqa: E501
# Enable the HTTP cache
# HTTPCACHE_ENABLED = True

# How long (in seconds) a cached response is considered fresh.
# 0 means “never expire” (i.e. always reuse until you manually clear the cache).
# HTTPCACHE_EXPIRATION_SECS = 24 * 3600  # one day

# Directory where cached responses are stored
# HTTPCACHE_DIR = "httpcache"

# Which HTTP status codes should *not* be cached.
# By default you’ll cache even 500s; you can blacklist 500,502,503, etc.
# HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504]

# Storage backend: the filesystem is the simplest.
# You can also swap in a DBM backend, or write your own.
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# (Optional) If you want cached responses to be gzipped on disk:
# HTTPCACHE_GZIP = True

# (Optional) Respect HTTP headers like Cache-Control / Expires:
# HTTPCACHE_POLICY = "scrapy.extensions.httpcache.RFC2616Policy"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# How verbose the logs are (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Turn on the retry middleware
RETRY_ENABLED = True

# Retry each failed request up to 2 extra times
RETRY_TIMES = 3

# Which response codes should trigger a retry
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408]

# Allow the crawler to follow HTTP 3xx redirects
REDIRECT_ENABLED = True

# Stop after following 20 redirects for a single request
REDIRECT_MAX_TIMES = 20

# Abort any request taking longer than 15 seconds
DOWNLOAD_TIMEOUT = 60

# Directory where Scrapy will save/resume crawl state
# JOBDIR = "crawls/thws-1"

# Default allowed length > 2083, 0 to disable it
URLLENGTH_LIMIT = 0
