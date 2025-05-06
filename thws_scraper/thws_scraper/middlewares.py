# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from urllib.parse import urlparse

# useful for handling different item types with a single interface
from scrapy import signals
from scrapy.downloadermiddlewares.robotstxt import RobotsTxtMiddleware
from twisted.internet.error import DNSLookupError


class ThwsScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ThwsScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


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

        if isinstance(exception, DNSLookupError):
            spider.logger.warning(f"[DNS] Could not resolve {request.url}")
        else:
            spider.logger.error(f"{request.url} failed: {exception!r}")

        if hasattr(spider, "reporter"):
            spider.reporter.bump("errors", domain)

            try:
                spider.update_rich_table()
            except Exception:
                pass

        return None


class RobotsBypassMiddleware(RobotsTxtMiddleware):
    """
    Bypass robots.txt only for certain subpaths like /fileadmin/.
    All other rules from robots.txt are still respected.
    """

    def process_request(self, request, spider):
        parsed = urlparse(request.url)

        # Allow /fileadmin/ paths unconditionally
        if parsed.path.startswith("/fileadmin/"):
            spider.logger.debug(f"Bypassing robots.txt for: {request.url}")
            return None  # skip the rest of this middleware

        # otherwise fall back to the normal robots.txt logic
        return super().process_request(request, spider)
