from pathlib import Path

from .thws_spider import ThwsSpider


class ThwsRescrapeSpider(ThwsSpider):
    name = "thws_rescrape"
    rules = []  # Dont follow links on rescrape

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rescrape_path = Path("result/rescrape_urls.txt")
        if rescrape_path.exists():
            with rescrape_path.open("r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
                if urls:
                    self.logger.info(f"Loaded {len(urls)} rescrape URLs from {rescrape_path}")
                    self.start_urls = urls
                else:
                    self.logger.warning(
                        f"No URLs found in {rescrape_path}, using default start_urls."
                    )
        else:
            self.logger.warning(f"{rescrape_path} does not exist, using default start_urls.")

    def parse(self, response):
        """
        This method is called for each of the start_urls.
        We delegate the response to the parse_item method from the parent class,
        which contains the actual parsing logic. We must `yield from` it
        as parse_item itself is a generator.
        """
        yield from self.parse_item(response)
