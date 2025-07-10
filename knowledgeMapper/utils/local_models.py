import asyncio

import config
import httpx
import torch
from langchain_huggingface import HuggingFaceEmbeddings

# Semaphore to throttle concurrency of embedding requests (avoids OOM)
_EMBED_SEMAPHORE = asyncio.Semaphore(config.EMBEDDING_CONCURRENCY)

# HuggingFace embeddings wrapper using LangChain's integration
_hf = HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL_NAME,
    encode_kwargs={"normalize_embeddings": True},  # Ensure unit-length vectors
    model_kwargs={"device": config.EMBEDDING_DEVICE},  # e.g., "cuda" or "cpu"
)

# Calculate and expose the dimensionality of the embedding space
EMBED_DIM = len(_hf.embed_query("test"))


class AsyncEmbedder:
    """
    Async-compatible, memory-safe wrapper for HuggingFace embedding generation.
    Uses:
    - semaphore to control parallelism,
    - `to_thread()` to move blocking code out of the main event loop,
    - torch.no_grad() and empty_cache() to reduce GPU pressure.
    """

    embedding_dim: int = EMBED_DIM

    async def __call__(self, texts: list[str]) -> list[list[float]]:
        async with _EMBED_SEMAPHORE:
            return await asyncio.to_thread(self._embed_chunked, texts)

    def _embed_chunked(self, texts: list[str]) -> list[list[float]]:
        # Split into batches and embed each chunk
        vecs: list[list[float]] = []
        for i in range(0, len(texts), config.EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + config.EMBEDDING_BATCH_SIZE]
            with torch.no_grad():  # No gradients needed for inference
                vecs.extend(_hf.embed_documents(batch))
            torch.cuda.empty_cache()  # Free VRAM after each batch (helps with OOM)
        return vecs


_async_embedder_instance = AsyncEmbedder()


async def embedding_wrapper_func(texts: list[str]) -> list[list[float]]:
    """Embedding API used by LightRAG (callable + exposes .embedding_dim)."""
    return await _async_embedder_instance(texts)


embedding_wrapper_func.embedding_dim = _async_embedder_instance.embedding_dim

# Exported function used by the rest of the app
embedding_func = embedding_wrapper_func


class OllamaLLM:
    """
    Async wrapper around Ollama's local LLM endpoint (`/api/generate`).
    Uses httpx for non-blocking HTTP requests.
    """

    async def __call__(
        self,
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict] | None = None,
        **kwargs,
    ) -> str:
        # Strip unused keys to avoid API incompatibilities
        for k in ("hashing_kv", "max_tokens", "response_format"):
            kwargs.pop(k, None)

        # Concatenate prompt components in proper order
        parts: list[str] = []
        if system_prompt:
            parts.append(system_prompt)
        if history_messages:
            # This part might need adjustment based on how you structure history
            parts.append("\n".join(m.get("content", "") for m in history_messages))
        parts.append(prompt)
        full_prompt = "\n".join(parts)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{config.OLLAMA_HOST}/api/generate",
                    json={
                        "model": config.OLLAMA_MODEL_NAME,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "num_ctx": config.OLLAMA_NUM_CTX,
                            "num_predict": config.OLLAMA_NUM_PREDICT,
                        },
                    },
                    timeout=120.0,  # Increased timeout for large models
                )
                response.raise_for_status()
                return response.json().get("response", "Error: Empty response from model.")
            except httpx.RequestError as exc:
                print(f"An error occurred while requesting {exc.request.url!r}.")
                return "Error: Could not connect to the language model."
            except httpx.HTTPStatusError as exc:
                print(
                    f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
                )
                return f"Error: Received status {exc.response.status_code} from the model."


__all__ = [
    "embedding_func",
    "OllamaLLM",
    "EMBEDDING_MODEL_NAME",
    "OLLAMA_MODEL_NAME",
]
