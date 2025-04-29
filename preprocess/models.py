import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RawPage(Base):
    __tablename__ = "raw_pages"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    url = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    title = Column(Text)
    text = Column(Text, nullable=False)
    date_scraped = Column(DateTime)
    date_updated = Column(DateTime)
    status = Column(Integer)
    lang = Column(String)
    parse_error = Column(Text)


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    raw_page_id = Column(Integer, ForeignKey("raw_pages.id", ondelete="CASCADE"))
    sequence_index = Column(Integer, default=0)
    text = Column(Text, nullable=False)
