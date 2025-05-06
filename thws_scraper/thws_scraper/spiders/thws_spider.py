import csv
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlparse

from itemadapter import ItemAdapter
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..parsers.html_parser import parse_html
from ..parsers.ical_parser import parse_ical
from ..parsers.pdf_parser import parse_pdf
from ..utils.env_override import get_setting
from ..utils.stats import StatsReporter
from ..utils.stats_server import StatsHTTPServer


class ThwsSpider(CrawlSpider):
    name = "thws"
    allowed_domains = ["thws.de"]
    start_urls = ["https://www.thws.de/", "https://fiw.thws.de/"]
    # follow links in the text to icals and pdf too
    rules = [
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                allow=[r"\.pdf$", r"\.ics$", r"/"],
            ),
            callback="parse_item",
            follow=True,
        )
    ]

    @classmethod
    def from_crawler(cls, crawler):
        spider = cls(settings=crawler.settings)
        spider.crawler = crawler
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def __init__(self, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings

        # stats & reporting
        self.reporter = StatsReporter()
        self.start_time = datetime.utcnow()

        self._follow_links = True

    def spider_opened(self):
        ts = self.start_time.strftime("%Y%m%d_%H%M%S")
        Path("result").mkdir(parents=True, exist_ok=True)
        log_filename = f"result/thws_{ts}.log"

        # Get log level from settings, fallback to WARNING
        log_level_str = get_setting(self.settings, "LOG_LEVEL", "WARNING", str).upper()
        log_level = getattr(logging, log_level_str)

        # Print log level to stdout
        print(f"Log level set to: {log_level_str}")
        self.logger.info(f"Spider started at {self.start_time.isoformat()}")

        # Suppress noisy readability logs
        logging.getLogger("readability.readability").setLevel(logging.ERROR)

        self.stats_server = StatsHTTPServer(self.reporter)
        self.stats_server.start()

        if get_setting(self.settings, "ENABLE_FILE_LOGGING", True, bool):
            fh = RotatingFileHandler(
                log_filename,
                maxBytes=10_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            fh.setLevel(log_level)
            fh.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            logging.getLogger().addHandler(fh)
            self.logger.info(f"File logging enabled → {log_filename}")
        else:
            self.logger.info("File logging disabled")

    def spider_closed(self, reason):
        """
        Called when the spider is closed.
        Converts the final stats to a CSV file if enabled.
        """
        total_runtime = datetime.utcnow() - self.start_time
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total runtime: {str(total_runtime).split('.')[0]}")
        self.stats_server.stop()

        if not get_setting(self.settings, "EXPORT_CSV_STATS", True, bool):
            self.logger.info("CSV export disabled.")
            return

        ts = self.start_time.strftime("%Y%m%d_%H%M%S")
        csv_path = f"result/stats_{ts}.csv"

        Path("result").mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Subdomain",
                    "Html",
                    "Pdf",
                    "Ical",
                    "Errors",
                    "Empty",
                    "Ignored",
                    "Bytes",
                ]
            )

            for domain, counters in sorted(self.reporter.per_domain.items()):
                writer.writerow(
                    [
                        domain,
                        counters.get("html", 0),
                        counters.get("pdf", 0),
                        counters.get("ical", 0),
                        counters.get("errors", 0),
                        counters.get("empty", 0),
                        counters.get("ignored", 0),
                        f"{counters.get('bytes', 0)/1024:.1f} KB",
                    ]
                )

        self.logger.info(f"Wrote stats table to {csv_path}")

    def parse_item(self, response):
        """
        Dispatch to the correct parser (HTML, PDF, iCal), and yield parsed items.
        Also extracts .pdf and .ics links from raw body and follows them.
        """
        domain = urlparse(response.url).netloc
        self.reporter.bump("bytes", domain, len(response.body))
        url_lower = response.url.lower()

        # only allow HTML pages, PDFs and iCal files
        ctype = (
            response.headers.get("Content-Type", b"").decode().split(";", 1)[0].lower()
        )
        if not (
            url_lower.endswith(".pdf")
            or url_lower.endswith(".ics")
            or "text/html" in ctype
        ):
            self.logger.debug(f"Ignored non-html/pdf/ics: {response.url}")
            self.reporter.bump("ignored", domain)
            return

        # Skip unwanted sites, eg. video files
        IGNORED_URL_PATTERNS = [
            "tx_fhwsvideo_frontend",
            "/videos/",
            "/wp-content/uploads/",
            "/login/",
        ]
        if any(pat in url_lower for pat in IGNORED_URL_PATTERNS):
            self.logger.debug(f"Ignored page by pattern: {response.url}")
            self.reporter.bump("ignored", domain)
            return

        # Choose parser
        if url_lower.endswith(".pdf") or "pdf" in ctype:
            items = parse_pdf(response)
            embedded_links = []
        elif url_lower.endswith(".ics") or ctype in (
            "text/calendar",
            "application/ical",
        ):
            items = parse_ical(response)
            embedded_links = []
        else:
            parsed = parse_html(response)
            if parsed is None:
                items = None
                embedded_links = []
            else:
                items, embedded_links = parsed

        if not items:
            self.reporter.bump("empty", domain)
        else:
            for item in items if isinstance(items, list) else [items]:
                adapter = ItemAdapter(item)
                item_type = adapter.get("type", "unknown")
                self.reporter.bump(item_type, domain)
                self.reporter.bump("total")
                yield item

        # Follow .pdf / .ics links extracted from the HTML page
        for link in embedded_links:
            yield response.follow(link, callback=self.parse_item)
