import json
import os
import sys
import uuid

import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- CLI Input ---
if len(sys.argv) < 2:
    print(f"Usage: python {sys.argv[0]} <chunks_file.json>")
    sys.exit(1)

CHUNKS_PATH = sys.argv[1]
COLLECTION_NAME = os.path.splitext(os.path.basename(CHUNKS_PATH))[0]
EMBED_MODEL_NAME = "BAAI/bge-m3"
EMBED_DIM = 1024
QDRANT_URL = "http://localhost:6333"

# --- Load Chunks ---
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# --- Load Embedding Model with CUDA ---
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = "mps"
else:
    device = "cpu"
print(f"🔥 Using device: {device}")
model = SentenceTransformer(EMBED_MODEL_NAME, device=device)

# --- Init Qdrant Client ---
qdrant = QdrantClient(url=QDRANT_URL)

# --- Create Collection ---
if qdrant.collection_exists(COLLECTION_NAME):
    qdrant.delete_collection(collection_name=COLLECTION_NAME)

qdrant.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
)


# --- Prepare and Upload Vectors ---
points = []
texts = [chunk["text"] for chunk in chunks]
embeddings = model.encode(texts, show_progress_bar=True, device=device)

for i, chunk in enumerate(chunks):
    vector = embeddings[i]
    payload = {
        "text": chunk["text"],
        "source": chunk["metadata"]["source"],
        "chunk_id": chunk["chunk_id"],
        "type": chunk["metadata"].get("type", "unknown"),
        "language": chunk["metadata"].get("lang", "unknown"),
    }

    points.append(PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload))

# --- Upload in Batches ---
BATCH_SIZE = 64
for i in tqdm(range(0, len(points), BATCH_SIZE), desc="Uploading to Qdrant"):
    batch = points[i : i + BATCH_SIZE]
    qdrant.upsert(collection_name=COLLECTION_NAME, points=batch)

print(f"✅ Uploaded {len(points)} chunks to Qdrant collection '{COLLECTION_NAME}'")
