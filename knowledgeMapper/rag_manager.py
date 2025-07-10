from typing import Dict

import config
from utils.local_models import OllamaLLM, embedding_func
from utils.mongo_vector_store import MongoVectorStore

_vector_store_instance: MongoVectorStore | None = None


async def get_rag_instance() -> MongoVectorStore:
    """
    Factory to load and cache the single, unified vector store instance.
    """
    global _vector_store_instance
    if _vector_store_instance:
        return _vector_store_instance

    _vector_store_instance = MongoVectorStore(
        db_name=config.MONGO_DB_NAME,
        collection_name=config.MONGO_VECTOR_COLLECTION,
        vector_index_name=config.MONGO_VECTOR_INDEX_NAME,
    )
    await _vector_store_instance.ainit()
    print("[*] MongoDB Vector Store instance loaded successfully.")
    return _vector_store_instance
