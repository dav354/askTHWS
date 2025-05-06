import atexit
import os
import signal
import subprocess
import time
import warnings

import requests
import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- Config ---
COLLECTION_NAME = "thws_data2_chunks"
QDRANT_URL = "http://localhost:6333"
EMBED_MODEL_NAME = "BAAI/bge-m3"
# OLLAMA_MODEL = "gemma:7b"
# OLLAMA_MODEL = "zephyr"
OLLAMA_MODEL = "mixtral"
TOP_K = 5

# --- Load Embedding Model ---
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = "mps"
else:
    device = "cpu"
print(f"🔥 Using device: {device}")
embedder = SentenceTransformer(EMBED_MODEL_NAME, device=device)

# --- Init Qdrant ---
client = QdrantClient(url=QDRANT_URL)

# --- Launch Ollama Server ---
ollama_process = subprocess.Popen(
    ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)


# Ensure Ollama server stops when FastAPI stops
def shutdown_ollama():
    print("🛑 Stopping Ollama server...")
    if os.name == "nt":
        ollama_process.terminate()
    else:
        os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)


atexit.register(shutdown_ollama)

# --- FastAPI ---
app = FastAPI()


class Question(BaseModel):
    query: str


@app.get("/metadata")
def get_metadata():
    commit_hash = subprocess.getoutput("git rev-parse HEAD")
    return {
        "model": OLLAMA_MODEL,
        "embedding_model": EMBED_MODEL_NAME,
        "commit_hash": commit_hash,
        "device": device,
    }


@app.post("/ask")
def ask_question(data: Question):
    start_time = time.time()
    query = data.query

    # --- Embed Query ---
    query_vec = embedder.encode(query, device=device)

    # --- Search Qdrant ---
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vec.tolist(),
        limit=TOP_K,
        with_payload=True,
    )

    # --- Deduplicate by Source ---
    unique_chunks = {}
    for res in search_results:
        src = res.payload["source"]
        if src not in unique_chunks:
            unique_chunks[src] = res

    context = "\n\n".join(res.payload["text"] for res in unique_chunks.values())

    # --- Prompt ---
    prompt = f"""
Du bist ein hilfreicher Assistent der Hochschule THWS.
Beantworte die folgende Frage basierend auf dem gegebenen Kontext.
Antworte ausschließlich auf Deutsch und fasse dich klar und präzise.
Wenn du es nicht weißt, sag "Ich weiß es leider nicht."

Kontext:
{context}

Frage:
{query}

Antwort:
"""

    # --- Call Ollama ---
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
    )

    answer = response.json().get("response", "").strip()
    calc_time = round(time.time() - start_time, 2)

    return {
        "question": query,
        "answer": answer,
        "sources": list(unique_chunks.keys()),
        "time_seconds": calc_time,
    }


# --- Run with: python api_server.py ---
if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
