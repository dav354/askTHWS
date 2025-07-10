import csv
from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..items import RawPageItem
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
    rules = [
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                allow=[r"\.pdf$", r"\.ics$", r"/"],
                deny_extensions=[],
            ),
            callback="parse_item",
            follow=True,
        )
    ]

    @classmethod
    def from_crawler(cls, crawler):
        spider = super().from_crawler(crawler)
        spider.tz = crawler.settings.get("APP_TZ")

        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)

        spider.ignored_url_patterns = crawler.settings.getlist("IGNORED_URL_PATTERNS_LIST", [])
        spider.soft_error_strings = [
            s.lower() for s in crawler.settings.getlist("SOFT_ERROR_STRINGS", [])
        ]

        spider.logger.info(
            f"Loaded {len(spider.ignored_url_patterns)} ignored URL patterns from settings."
        )
        spider.logger.info(
            f"Loaded {len(spider.soft_error_strings)} soft error strings from settings."
        )

        return spider

    def __init__(self, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reporter = StatsReporter()
        self._follow_links = True

    def spider_opened(self, spider):
        self.start_time = datetime.now(self.tz)
        self.reporter.set_start_time(self.start_time)

        Path("result").mkdir(parents=True, exist_ok=True)
        self.logger.info(
            f"Spider '{spider.name}' starting",
            extra={"spider_name": spider.name, "start_time_iso": self.start_time.isoformat()},
        )
        self.stats_server = StatsHTTPServer(self.reporter)
        self.stats_server.start()
        self.logger.info("Stats server started", extra={"url": "http://0.0.0.0:7000/live"})

    def spider_closed(self, reason):
        total_runtime = datetime.now(self.tz) - self.start_time
        self.logger.info(
            "Spider closed",
            extra={"reason": reason, "runtime_seconds": total_runtime.total_seconds()},
        )

        if hasattr(self, "stats_server") and self.stats_server:
            self.stats_server.stop()

        if not get_setting(self.settings, "EXPORT_CSV_STATS", True, bool):
            self.logger.info("CSV export disabled by EXPORT_CSV_STATS setting.")
            return

        ts = self.start_time.strftime("%Y%m%d_%H%M%S")
        csv_path = Path("result") / f"stats_{ts}.csv"

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                header = [
                    "Subdomain",
                    "Html",
                    "Pdf",
                    "Ical",
                    "Errors",
                    "Empty",
                    "Ignored",
                    "Bytes",
                ]
                writer.writerow(header)
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
            self.logger.info("Wrote stats table to CSV", extra={"csv_path": str(csv_path)})
        except IOError as e:
            self.logger.error(
                "Failed to write stats CSV", extra={"csv_path": str(csv_path), "error": str(e)}
            )

    def parse_item(self, response):
        domain = urlparse(response.url).netloc
        self.reporter.bump("bytes", domain, len(response.body))
        url_lower = response.url.lower()
        ctype = response.headers.get("Content-Type", b"").decode().split(";", 1)[0].lower()

        if hasattr(self, "ignored_url_patterns") and any(
            pat in url_lower for pat in self.ignored_url_patterns
        ):
            matched_pattern = next(
                (pat for pat in self.ignored_url_patterns if pat in url_lower), "Unknown pattern"
            )
            self.logger.info(
                "Skipped page: Ignored URL pattern",
                extra={
                    "event_type": "page_skipped",
                    "url": response.url,
                    "reason": "ignored_url_pattern",
                    "pattern_matched": matched_pattern,
                },
            )
            self.reporter.bump("ignored", domain)
            return

        items_to_yield: List[RawPageItem] = []
        embedded_links: List[str] = []

        is_pdf = url_lower.endswith(".pdf") or "application/pdf" in ctype
        is_ics = url_lower.endswith(".ics") or ctype in (
            "text/calendar",
            "application/ical",
            "application/octet-stream+ics",
        )
        is_html = "text/html" in ctype

        if is_pdf:
            self.reporter.bump("pdf", domain)
            item = parse_pdf(response, self.tz)
            if item:
                items_to_yield.append(item)
            else:
                self.logger.warning("PDF parser returned no item", extra={"url": response.url})
        elif is_ics:
            self.reporter.bump("ical", domain)
            item = parse_ical(response, self.tz)
            if item:
                items_to_yield.append(item)
            else:
                self.logger.warning("iCAL parser returned no item", extra={"url": response.url})
        elif is_html:
            if not hasattr(self, "soft_error_strings"):
                self.logger.warning(
                    "soft_error_strings not found on spider instance. Using empty list.",
                    extra={"url": response.url},
                )
                current_soft_error_strings = []
            else:
                current_soft_error_strings = self.soft_error_strings

            parsed_output = parse_html(
                response, soft_error_strings=current_soft_error_strings, tz=self.tz
            )
            if parsed_output:
                html_items, embedded_links = parsed_output
                if html_items:
                    items_to_yield.extend(html_items)
                    self.reporter.bump("html", domain, n=len(html_items))
                else:
                    self.reporter.bump("empty", domain)
                    self.logger.info(
                        "HTML page yielded no main items but processing continued (e.g., found links)",
                        extra={"url": response.url},
                    )
            else:
                self.reporter.bump("empty", domain)
        else:
            self.logger.info(
                "Skipped page: Unhandled content type",
                extra={
                    "event_type": "page_skipped",
                    "url": response.url,
                    "reason": "unhandled_content_type",
                    "content_type": ctype,
                },
            )
            self.reporter.bump("ignored", domain)
            return

        if not items_to_yield and not (is_html and embedded_links):
            if not is_html:
                self.reporter.bump("empty", domain)
                self.logger.info(
                    "No items yielded from non-HTML page and no embedded links followed",
                    extra={
                        "event_type": "item_yield_empty_final",
                        "url": response.url,
                        "content_type": ctype,
                        "reason": f"{ctype}_parser_returned_no_item_or_unhandled",
                    },
                )

        for item_obj in items_to_yield:
            yield item_obj
            self.reporter.bump("total_items_yielded", domain)

        for link in embedded_links:
            yield response.follow(link, callback=self.parse_item)
