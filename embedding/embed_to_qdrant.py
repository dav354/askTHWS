#!/usr/bin/env python3
"""
embed_to_qdrant.py

Reads a JSONL of text chunks, computes embeddings via a SentenceTransformer,
and uploads them in batches to a Qdrant collection.

Usage:
    python embed_to_qdrant.py <chunks_file.jsonl>
"""

import json
import os
import sys
import uuid

import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def upload_batch(
    qdrant_client: QdrantClient,
    collection_name: str,
    chunks_batch: list[dict],
    embeddings_batch: list[list[float]],
) -> None:
    """
    Upload a batch of embeddings and payloads to Qdrant.

    Args:
        qdrant_client: Initialized QdrantClient instance.
        collection_name: Name of the Qdrant collection.
        chunks_batch: List of chunk dicts
            (each must have "text", "metadata", "chunk_id").
        embeddings_batch: Corresponding list of embedding vectors.
    """
    points = []
    for chunk, vector in zip(chunks_batch, embeddings_batch):
        payload = {
            "text": chunk["text"],
            "source": chunk["metadata"].get("source"),
            "chunk_id": chunk["chunk_id"],
            "type": chunk["metadata"].get("type", "unknown"),
            "language": chunk["metadata"].get("lang", "unknown"),
        }
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload,
            )
        )

    qdrant_client.upsert(collection_name=collection_name, points=points)


def main() -> None:
    """
    Entry point: parse arguments, initialize model and Qdrant collection,
    then read chunks, batch embeddings, and upload to Qdrant.
    """
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <chunks_file.jsonl>")
        sys.exit(1)

    chunks_path = sys.argv[1]
    if not os.path.isfile(chunks_path):
        print(f"❌ File not found: {chunks_path}")
        sys.exit(1)

    collection_name = os.path.splitext(os.path.basename(chunks_path))[0]
    embed_model_name = "BAAI/bge-m3"
    embed_dim = 1024
    qdrant_url = "http://qadrant:6333"
    batch_size = 64

    # Choose device
    device = (
        "cuda"
        if torch.cuda.is_available()
        else ("mps" if torch.backends.mps.is_available() else "cpu")
    )
    print(f"🔥 Using device: {device}")

    # Load the embedding model
    model = SentenceTransformer(embed_model_name, device=device)

    # Initialize Qdrant client and (re)create collection
    qdrant = QdrantClient(url=qdrant_url)
    if qdrant.collection_exists(collection_name):
        print(f"⚠️ Deleting existing collection '{collection_name}'...")
        qdrant.delete_collection(collection_name=collection_name)

    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=embed_dim, distance=Distance.COSINE),
    )

    # Read chunks, compute embeddings in batches, upload
    points_batch: list[dict] = []
    texts_batch: list[str] = []
    total_uploaded = 0

    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="🔄 Reading chunks"):
            line = line.strip()
            if not line:
                continue

            chunk = json.loads(line)
            text = chunk.get("text", "")
            if not text:
                continue

            texts_batch.append(text)
            points_batch.append(chunk)

            if len(texts_batch) >= batch_size:
                embeddings = model.encode(texts_batch, device=device)
                upload_batch(qdrant, collection_name, points_batch, embeddings)
                total_uploaded += len(texts_batch)
                points_batch.clear()
                texts_batch.clear()

    # Upload any remainder
    if texts_batch:
        embeddings = model.encode(texts_batch, device=device)
        upload_batch(qdrant, collection_name, points_batch, embeddings)
        total_uploaded += len(texts_batch)

    print(
        f"✅ Uploaded {total_uploaded} chunks "
        f"to Qdrant collection '{collection_name}'"
    )


if __name__ == "__main__":
    main()
