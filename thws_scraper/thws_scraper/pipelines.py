# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import json
import os
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .items import DocumentChunkItem, RawPageItem
from .models import Base, Chunk, Job, RawPage


class RawOutputPipeline:
    """
    Dumps every RawPageItem as one line in data_raw_<TIMESTAMP>.jsonl
    """

    def open_spider(self, spider):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.raw_path = f"result/data_raw_{ts}.jsonl"
        spider.logger.info(f"[RawOutput] opening {self.raw_path}")
        self.raw_file = open(self.raw_path, "w", encoding="utf-8")

    def close_spider(self, spider):
        spider.logger.info(f"[RawOutput] closing {self.raw_path}")
        self.raw_file.close()

    def process_item(self, item, spider):
        if isinstance(item, RawPageItem):
            line = json.dumps(dict(item), ensure_ascii=False)
            self.raw_file.write(line + "\n")
        return item


class ORMPostgresPipeline:
    """
    - on spider_opened: make a new Job row.
    - on RawPageItem: INSERT into raw_pages.
    - on DocumentChunkItem: INSERT into chunks.
    - on spider_closed: mark Job finished.
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def __init__(self):
        user = os.getenv("POSTGRES_USER", "scraper")
        pw = os.getenv("POSTGRES_PASSWORD", "secret")
        db = os.getenv("POSTGRES_DB", "scraperdb")
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")

        db_url = f"postgresql://{user}:{pw}@{host}:{port}/{db}"
        self.engine = create_engine(db_url, echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def open_spider(self, spider):
        """
        Start a DB session and create a Job.
        """
        self.session = self.Session()
        job = Job(status="running", started_at=datetime.utcnow())
        self.session.add(job)
        self.session.commit()
        self.job = job
        spider._rawpage_map = {}

    def process_item(self, item, spider):
        """
        Route items to the correct table.
        """
        if isinstance(item, RawPageItem):
            rp = RawPage(
                job_id=self.job.id,
                url=item["url"],
                type=item["type"],
                title=item["title"],
                text=item["text"],
                date_scraped=item["date_scraped"],
                date_updated=item["date_updated"],
                status=item["status"],
                lang=item["lang"],
                parse_error=item.get("parse_error"),
            )
            self.session.add(rp)
            self.session.flush()  # assigns rp.id
            spider._rawpage_map[rp.url] = rp.id
            return item

        if isinstance(item, DocumentChunkItem):
            raw_id = spider._rawpage_map.get(item["source_url"])
            if raw_id is None:
                raise DropItem(f"No RawPage for chunk {item['chunk_id']}")
            ch = Chunk(
                id=item["chunk_id"],
                job_id=self.job.id,
                raw_page_id=raw_id,
                sequence_index=item.get("sequence_index", 0),
                text=item["text"],
            )
            self.session.add(ch)
            return item

        return item

    def close_spider(self, spider):
        """
        Mark the Job finished and commit.
        """
        self.job.status = "finished"
        self.job.finished_at = datetime.utcnow()
        self.session.commit()
        self.session.close()
