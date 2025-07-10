import logging
from urllib.parse import urlparse

from scrapy import signals
from scrapy.downloadermiddlewares.robotstxt import RobotsTxtMiddleware
from twisted.internet.error import DNSLookupError


class ThwsScraperSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        spider.logger.error(
            "Exception processing spider output",
            extra={
                "event_type": "spider_exception",
                "url": response.url if response else "N/A",
                "spider_name": spider.name,
                "middleware": self.__class__.__name__,
                "error": str(exception),
                "exception_type": type(exception).__name__,
                "traceback": (
                    logging.Formatter().formatException(logging.sys.exc_info())
                    if logging.sys
                    else str(exception)
                ),
            },
        )
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info(
            "Spider middleware opened",
            extra={
                "event_type": "middleware_opened",
                "spider_name": spider.name,
                "middleware_class": self.__class__.__name__,
            },
        )


class ThwsScraperDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info(
            "Downloader middleware opened",
            extra={
                "event_type": "middleware_opened",
                "spider_name": spider.name,
                "middleware_class": self.__class__.__name__,
            },
        )


class ThwsErrorMiddleware:
    """
    Catch downloader errors (DNS, timeouts, etc.), log and count them,
    then swallow so the crawl continues.
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_exception(self, request, exception, spider):

        domain = urlparse(request.url).netloc
        exception_type_name = type(exception).__name__
        error_message = str(exception)

        log_details = {
            "url": request.url,
            "spider_name": spider.name,
            "middleware_class": self.__class__.__name__,
            "error": error_message,
            "exception_type": exception_type_name,
            "domain": domain,
        }

        if isinstance(exception, DNSLookupError):
            log_details["event_type"] = "dns_error"
            spider.logger.warning("DNS lookup failed for request", extra=log_details)
        else:
            log_details["event_type"] = "downloader_exception_general"
            spider.logger.error("Unhandled downloader exception", extra=log_details)

        if hasattr(spider, "reporter") and callable(getattr(spider, "reporter", None).bump):
            spider.reporter.bump("errors", domain)
        else:
            spider.logger.warning(
                "Spider reporter not found or bump method is not callable, cannot bump error stat.",
                extra={"url": request.url, "middleware_class": self.__class__.__name__},
            )

        return None


class RobotsBypassMiddleware(RobotsTxtMiddleware):
    """
    Bypass robots.txt only for certain subpaths like /fileadmin/.
    All other rules from robots.txt are still respected.
    """

    def process_request(self, request, spider):
        parsed_url = urlparse(request.url)

        if parsed_url.path.startswith("/fileadmin/"):
            spider.logger.debug(
                "Bypassing robots.txt check for URL",
                extra={
                    "event_type": "robots_txt_bypass",
                    "url": request.url,
                    "reason": "path_starts_with_fileadmin",
                    "middleware_class": self.__class__.__name__,
                },
            )
            return None

        return super().process_request(request, spider)
