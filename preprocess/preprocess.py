#!/usr/bin/env python3
"""
preprocess_and_chunk.py

Read raw_pages from Postgres, chunk their text,
store the chunks back to Postgres, and expose live progress via SSE.
"""

import os
import threading
import time
import uuid

from flask import Flask, Response
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langdetect import DetectorFactory, detect
from models import Chunk, RawPage
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Make langdetect deterministic
DetectorFactory.seed = 42

# Load Postgres connection settings
DB_USER = os.getenv("POSTGRES_USER", "scraper")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "secret")
DB_NAME = os.getenv("POSTGRES_DB", "scraperdb")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL, echo=False, future=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Progress stats
progress = {
    "total_docs": 0,
    "total_chunks": 0,
    "done": False,
}

# Start Flask app
app = Flask(__name__)


def chunk_documents():
    """Main chunking logic."""
    session = Session()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    raw_pages = session.execute(select(RawPage)).scalars().all()
    progress["total_docs"] = len(raw_pages)

    for page in raw_pages:
        if not page.text.strip():
            continue

        try:
            lang = detect(page.text)
        except Exception:
            lang = "unknown"

        metadata = {
            "source": page.url,
            "title": page.title,
            "type": page.type,
            "date_updated": page.date_updated,
            "lang": lang,
        }

        chunks = splitter.split_text(page.text)
        for chunk_text in chunks:
            chunk = Chunk(
                id=str(uuid.uuid4()),
                job_id=page.job_id,
                raw_page_id=page.id,
                sequence_index=progress["total_chunks"],  # just sequential number
                text=chunk_text,
                source=metadata["source"],
                title=metadata["title"],
                type=metadata["type"],
                date_updated=metadata["date_updated"],
                lang=metadata["lang"],
            )
            session.add(chunk)
            progress["total_chunks"] += 1

        session.commit()

    progress["done"] = True
    session.close()


def run_chunking_background():
    threading.Thread(target=chunk_documents, daemon=True).start()


@app.route("/events")
def sse_events():
    def event_stream():
        while not progress["done"]:
            yield f"data: {progress}\n\n"
            time.sleep(1)
        yield f"data: {progress}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    print("🚀 Starting preprocessing...")

    run_chunking_background()

    app.run(host="0.0.0.0", port=7001, threaded=True)
