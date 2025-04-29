import uuid

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    raw_page_id = Column(Integer, ForeignKey("raw_pages.id", ondelete="CASCADE"))
    sequence_index = Column(Integer, default=0)
    text = Column(Text, nullable=False)
