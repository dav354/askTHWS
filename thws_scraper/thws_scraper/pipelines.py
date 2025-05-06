# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import hashlib
import json
import os
import uuid
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langdetect import DetectorFactory, detect
from scrapy.exceptions import DropItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .items import DocumentChunkItem, RawPageItem
from .models import Base, Chunk, Job, RawPage

# make langdetect deterministic
DetectorFactory.seed = 42


def get_engine_from_env():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")


class SQLAlchemyPipelineBase:
    def open_spider(self, spider):
        engine = get_engine_from_env()
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        self.session = self.Session()

        # Create a Job record
        self.job = Job()
        self.session.add(self.job)
        self.session.commit()
        spider.logger.info(f"[DB] Created job with ID {self.job.id}")
        spider.job_id = self.job.id

    def close_spider(self, spider):
        self.job.finished_at = datetime.utcnow()
        self.job.status = "finished"
        self.session.commit()
        self.session.close()
        spider.logger.info(
            f"[DB] Closed session and marked job {self.job.id} as finished"
        )


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
            # Convert all datetime fields to ISO strings
            serializable_item = {
                k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in dict(item).items()
            }
            line = json.dumps(serializable_item, ensure_ascii=False)
            self.raw_file.write(line + "\n")
        return item


class RawPostgresPipeline(SQLAlchemyPipelineBase):
    def process_item(self, item, spider):
        if not isinstance(item, RawPageItem):
            return item

        lang = item.get("lang")
        if not lang:
            try:
                lang = detect(item.get("text") or "")
            except Exception:
                lang = "unknown"

        raw_page = RawPage(
            job_id=self.job.id,
            url=item["url"],
            type=item.get("type", "unknown"),
            title=item.get("title"),
            text=item.get("text"),
            date_scraped=datetime.utcnow(),
            date_updated=item.get("date_updated"),
            status=item.get("status"),
            lang=lang,
            parse_error=item.get("parse_error"),
        )

        self.session.add(raw_page)
        self.session.commit()
        item["db_id"] = raw_page.id  # Pass this ID to chunking pipeline if needed

        return item


class ChunkingOutputPipeline:
    """
    Splits each RawPageItem into chunks, dedupes by SHA-256, writes each
    DocumentChunkItem to data_chunks_<TIMESTAMP>.jsonl, and then re-emits
    the original RawPageItem.
    """

    def __init__(self, chunk_size, chunk_overlap):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.seen_hashes = set()

    @classmethod
    def from_crawler(cls, crawler):
        cs = crawler.settings.getint("CHUNK_SIZE", 1000)
        co = crawler.settings.getint("CHUNK_OVERLAP", 100)
        return cls(cs, co)

    def open_spider(self, spider):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.chunks_path = f"result/data_chunks_{ts}.jsonl"
        spider.logger.info(f"[ChunksOutput] opening {self.chunks_path}")
        self.chunks_file = open(self.chunks_path, "w", encoding="utf-8")

    def close_spider(self, spider):
        spider.logger.info(f"[ChunksOutput] closing {self.chunks_path}")
        self.chunks_file.close()

    def process_item(self, item, spider):
        # Only handle RawPageItem
        if not isinstance(item, RawPageItem):
            return item

        text = (item.get("text") or "").strip()
        if not text:
            raise DropItem(f"Empty text - dropping {item['url']}")

        # Determine language: use item.lang if present, otherwise detect on text
        lang = item.get("lang")
        if not lang:
            try:
                lang = detect(text)
            except Exception:
                lang = "unknown"

        # Split into chunks
        chunks = self.splitter.split_text(text)
        for chunk_text in chunks:
            digest = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            if digest in self.seen_hashes:
                continue
            self.seen_hashes.add(digest)

            chunk_item = DocumentChunkItem(
                chunk_id=str(uuid.uuid4()),
                text=chunk_text,
                source_url=item["url"],
                title=item.get("title"),
                date_updated=item.get("date_updated"),
                lang=lang,
            )

            # Write out chunk
            serializable_item = {
                k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in dict(chunk_item).items()
            }
            line = json.dumps(serializable_item, ensure_ascii=False)
            self.chunks_file.write(line + "\n")

        return item


class ChunkingPostgresPipeline(SQLAlchemyPipelineBase):
    def __init__(self, chunk_size, chunk_overlap):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.seen_hashes = set()

    @classmethod
    def from_crawler(cls, crawler):
        cs = crawler.settings.getint("CHUNK_SIZE", 1000)
        co = crawler.settings.getint("CHUNK_OVERLAP", 100)
        return cls(cs, co)

    def open_spider(self, spider):
        super().open_spider(spider)

    def process_item(self, item, spider):
        from .items import RawPageItem

        if not isinstance(item, RawPageItem):
            return item

        text = (item.get("text") or "").strip()
        if not text:
            raise DropItem(f"Empty text - dropping {item['url']}")

        lang = item.get("lang")
        if not lang:
            try:
                lang = detect(text)
            except Exception:
                lang = "unknown"

        chunks = self.splitter.split_text(text)
        for idx, chunk_text in enumerate(chunks):
            digest = hashlib.sha256(
                (str(self.job.id) + chunk_text).encode("utf-8")
            ).hexdigest()
            if digest in self.seen_hashes:
                continue
            self.seen_hashes.add(digest)

            chunk = Chunk(
                id=uuid.uuid4(),
                job_id=self.job.id,
                raw_page_id=item["db_id"],
                sequence_index=idx,
                text=chunk_text,
                lang=lang,
                created_at=datetime.utcnow(),
            )

            self.session.add(chunk)

        self.session.commit()
        return item
