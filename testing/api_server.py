# File: api_server.py
# DEBUGGING VERSION: Hardcoding environment variables to test Neo4j connection.

import time
import torch
import subprocess
import atexit
import os
import signal
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any

# ==============================================================================
# TEMPORARY DEBUGGING STEP
# We are setting the environment variables directly in the code to bypass any
# potential issues with the .env file.
#
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledgeMapper.utils.local_models import embedding_func, OllamaLLM
from knowledgeMapper.retrieval import prepare_and_execute_retrieval
from knowledgeMapper import rag_manager
from knowledgeMapper import config



# --- Device Info ---
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔥 Using device: {device}")


# --- FastAPI App Initialization ---
app = FastAPI(
    title="THWS KG-RAG API (Final Architecture)",
    description="Ein API-Server, der die stabile `aquery`-Methode mit einem intelligenten Prompt für maximale Antwortqualität und Transparenz verwendet.",
    version="18.0.3_debug",  # Version bumped for debug
)


class Question(BaseModel):
    query: str


# --- Ollama Background Server Management ---
print("🚓 Starting Ollama server in the background...")
ollama_process = subprocess.Popen(
    ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    preexec_fn=os.setsid if os.name != 'nt' else None
)


@atexit.register
def shutdown_ollama():
    """Function to gracefully shut down the Ollama server process."""
    print("Shutting down Ollama server...")
    if ollama_process:
        try:
            if os.name == 'nt':
                ollama_process.terminate()
            else:
                os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)
            ollama_process.wait(timeout=5)
            print("🚓 Ollama server stopped successfully.")
        except Exception as e:
            print(f"Could not stop Ollama server gracefully: {e}")


# --- API Endpoints ---
@app.post("/ask")
async def ask(data: Question, request: Request):
    """
    Implements a controlled query pipeline by delegating to the retrieval module.
    """
    start_time = time.time()
    print(f"\n--- New Request ---")
    print(f"Received German query: '{data.query}'")
    try:
        # Delegate the entire logic to the retrieval function
        final_answer = await prepare_and_execute_retrieval(
            user_query=data.query,
        )

        duration = round(time.time() - start_time, 2)
        print(f"--- Request completed in {duration} seconds. ---")

        return {
            "question": data.query,
            "answer": final_answer,
            "duration_seconds": duration,
        }
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error. Details: {e}")


@app.get("/")
def read_root():
    """Root endpoint providing basic information about the API."""
    return {"message": "Welcome to the THWS KG-RAG API (Final Architecture)."}


@app.get("/metadata")
def metadata(request: Request):
    """
Provides metadata about the running service."""

    return {
        "embedding_model": config.EMBEDDING_MODEL_NAME,
        "llm_model": config.OLLAMA_MODEL_NAME,
        "device": device,
    }


# --- Run FastAPI Server ---
if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)

