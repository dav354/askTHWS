# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RawPageItem(scrapy.Item):
    """The full text + metadata for one fetched page or PDF."""

    url = scrapy.Field()
    type = scrapy.Field()  # "html" | "pdf" | "ical"
    title = scrapy.Field()
    text = scrapy.Field()
    date_scraped = scrapy.Field()
    date_updated = scrapy.Field()
    status = scrapy.Field()
    lang = scrapy.Field()
    parse_error = scrapy.Field()
    db_id = scrapy.Field()


class DocumentChunkItem(scrapy.Item):
    """One deduped chunk of a RawPageItem, ready for embedding."""

    chunk_id = scrapy.Field()
    text = scrapy.Field()
    source_url = scrapy.Field()
    title = scrapy.Field()
    date_updated = scrapy.Field()
    lang = scrapy.Field()
    embedding = scrapy.Field()
    kg_triples = scrapy.Field()
