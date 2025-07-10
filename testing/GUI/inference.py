# inference.py
import time

import requests
import torch
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# --- Config ---
API_URL = "http://localhost:11434/api/generate"
COLLECTION = "thws_data2_chunks"
QDRANT_URL = "http://localhost:6333"
EMBED_MODEL = "BAAI/bge-m3"
TOP_K = 3

# Device
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

# Init
embedder = SentenceTransformer(EMBED_MODEL, device=device)
client = QdrantClient(url=QDRANT_URL)


def get_context(question: str, top_k: int = TOP_K) -> str:
    """Sucht in Qdrant die relevantesten Chunks und gibt sie als Text-Block zurück."""
    q_vec = embedder.encode(question, device=device)
    hits = client.search(
        collection_name=COLLECTION,
        query_vector=q_vec.tolist(),
        limit=top_k,
        with_payload=True,
    )
    # Dedupliziere nach source
    unique = {}
    for hit in hits:
        src = hit.payload["source"]
        if src not in unique:
            unique[src] = hit
    return "\n\n".join(h.payload["text"] for h in unique.values())


def query_model(question: str, context: str, model_name: str = "gemma3:27b") -> str:
    prompt = f"""
Du bist ein hochintelligenter und präziser Assistent der Hochschule THWS.
Nutze ausschließlich die unten stehenden Kontextinformationen, um die Frage zu beantworten.
Wenn der Kontext nicht ausreicht, antworte mit "Diese Frage kann ich leider nicht beantworten."

Kontext:
{context}

Frage:
{question}

Antwort:
"""
    resp = requests.post(
        API_URL,
        json={"model": model_name, "prompt": prompt, "stream": False},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()
