import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    status = Column(String, nullable=False, default="running")
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at = Column(DateTime(timezone=True))

    raw_pages = relationship(
        "RawPage", back_populates="job", cascade="all, delete-orphan"
    )
    chunks = relationship("Chunk", back_populates="job", cascade="all, delete-orphan")


class RawPage(Base):
    __tablename__ = "raw_pages"
    __table_args__ = (
        # index on job_id for faster lookups when querying pages by job
        Index("ix_raw_pages_job_id", "job_id"),
    )

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    title = Column(Text)
    text = Column(Text, nullable=False)
    date_scraped = Column(DateTime(timezone=True), nullable=False)
    date_updated = Column(DateTime(timezone=True))
    status = Column(Integer)
    lang = Column(String)
    parse_error = Column(Text)

    job = relationship("Job", back_populates="raw_pages")
    chunks = relationship(
        "Chunk", back_populates="raw_page", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_raw_page_id", "raw_page_id"),
        Index("ix_chunks_job_id", "job_id"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    raw_page_id = Column(
        Integer, ForeignKey("raw_pages.id", ondelete="CASCADE"), nullable=False
    )
    raw_page = relationship("RawPage", back_populates="chunks")
    job = relationship("Job", back_populates="chunks")
    sequence_index = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    lang = Column(String)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
