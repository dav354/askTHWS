#!/usr/bin/env python3
"""
embed_to_qdrant.py

Reads chunks from Postgres, computes embeddings using a SentenceTransformer,
and uploads them to Qdrant collection with live SSE progress.
"""

import os
import threading
import time
import uuid
from typing import List

import torch
from flask import Flask, Response
from models import Chunk
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# DB Config
DB_USER = os.getenv("POSTGRES_USER", "scraper")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "secret")
DB_NAME = os.getenv("POSTGRES_DB", "scraperdb")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connect to DB
engine = create_engine(DB_URL, echo=False, future=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)

# Qdrant Config
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

# Embedding model config
EMBED_MODEL_NAME = "BAAI/bge-m3"
EMBED_DIM = 1024
BATCH_SIZE = 64

# Progress
progress = {
    "total_chunks": 0,
    "chunks_uploaded": 0,
    "done": False,
}


def embed_and_upload():
    """Load chunks from Postgres, embed, and upload to Qdrant."""
    device = (
        "cuda"
        if torch.cuda.is_available()
        else ("mps" if torch.backends.mps.is_available() else "cpu")
    )
    print(f"🔥 Using device: {device}")

    model = SentenceTransformer(EMBED_MODEL_NAME, device=device)
    session = Session()

    chunks: List[Chunk] = session.execute(select(Chunk)).scalars().all()
    progress["total_chunks"] = len(chunks)

    if not chunks:
        print("⚠️ No chunks found.")
        progress["done"] = True
        return

    collection_name = "chunks_collection"
    qdrant = QdrantClient(url=QDRANT_URL)

    if qdrant.collection_exists(collection_name):
        print(f"⚠️ Deleting existing collection '{collection_name}'...")
        qdrant.delete_collection(collection_name=collection_name)

    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )

    batch_texts = []
    batch_chunks = []

    for chunk in chunks:
        batch_texts.append(chunk.text)
        batch_chunks.append(chunk)

        if len(batch_texts) >= BATCH_SIZE:
            _upload_batch(qdrant, collection_name, model, batch_chunks, batch_texts)
            batch_texts.clear()
            batch_chunks.clear()

    if batch_texts:
        _upload_batch(qdrant, collection_name, model, batch_chunks, batch_texts)

    progress["done"] = True
    session.close()


def _upload_batch(
    qdrant: QdrantClient,
    collection_name: str,
    model: SentenceTransformer,
    batch_chunks: List[Chunk],
    batch_texts: List[str],
):
    embeddings = model.encode(batch_texts)
    points = []
    for chunk, vector in zip(batch_chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk.text,
                    "raw_page_id": chunk.raw_page_id,
                    "chunk_id": str(chunk.id),
                },
            )
        )

    qdrant.upsert(collection_name=collection_name, points=points)
    progress["chunks_uploaded"] += len(batch_chunks)


def run_embedder_background():
    threading.Thread(target=embed_and_upload, daemon=True).start()


# Tiny Flask SSE server
app = Flask(__name__)


@app.route("/events")
def sse_events():
    def event_stream():
        while not progress["done"]:
            yield f"data: {progress}\n\n"
            time.sleep(1)
        yield f"data: {progress}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    print("🚀 Starting embedding...")
    run_embedder_background()
    app.run(host="0.0.0.0", port=7002, threaded=True)
