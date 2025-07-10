# Scrapy settings for thws_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

tz_name = os.getenv("APP_TIMEZONE", "Europe/Berlin")
APP_TZ = ZoneInfo(tz_name)
print(f"INFO: Using timezone: {tz_name}")

RESULTS_DIR = Path(__file__).resolve().parent.parent / "result"
RESULTS_DIR.mkdir(exist_ok=True)
timestamp = datetime.now(APP_TZ).strftime("%Y%m%d_%H%M%S")
LOG_FILE_PATH = RESULTS_DIR / f"scrapy_log_{timestamp}.jsonl"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_FILE_PATH),
            "formatter": "json",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "scrapy": {"propagate": True},
        "thws": {"propagate": True},
        "thws_scraper": {"propagate": True},
    },
}


# ##################################################
# Custom values; might be configureable via env tbd
# ##################################################

ENABLE_FILE_LOGGING = True
EXPORT_CSV_STATS = True

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")

MONGO_PAGES_COLLECTION = "pages"
MONGO_FILES_COLLECTION = "files"

SOFT_ERROR_STRINGS = [
    "diese seite existiert nicht",
    "this page does not exist",
    "seite nicht gefunden",
    "not found",
    "404",
    "sorry, there is no translation for this news-article.",
    "studierende melden sich mit ihrer k-nummer als benutzername am e-learning system an.",
    (
        "falls sie die seitenadresse manuell in ihren browser eingegeben haben,"
        "kontrollieren sie bitte die korrekte schreibweise."
    ),
    "aktuell keine einträge vorhanden",
    "sorry, there are no translated news-articles in this archive period",
]

IGNORED_URL_PATTERNS_LIST = [
    "tx_fhwsvideo_frontend",
    "/videos/",
    "/wp-content/uploads/",
    "/login/",
]

# ##################################################

# Identifier for your bot. Used in logs, the default User-Agent header, etc.
BOT_NAME = "thws_scraper"

# Where Scrapy will look for your Spider classes
SPIDER_MODULES = ["thws_scraper.spiders"]
NEWSPIDER_MODULE = "thws_scraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "thws-scraper-bot/0.4.0"

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
    "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": None,  # disable the built-in
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
    "thws_scraper.pipelines.MongoPipeline": 100,
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


import logging  # noqa 402
import logging.config  # noqa 402

from scrapy.utils.log import configure_logging  # noqa 402

configure_logging()
logging.root.handlers.clear()
logging.config.dictConfig(LOGGING)
