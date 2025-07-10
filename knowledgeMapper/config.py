import os
from pathlib import Path

# Language selection for filtering documents (used in mongo_loader or processing)
LANGUAGE = os.getenv("LANGUAGE", "de").lower()  # 'all', 'de', or 'en'

# Language for LLM summarization tasks
SUMMARY_LANGUAGE = os.getenv("SUMMARY_LANGUAGE", "German")
os.environ['SUMMARY_LANGUAGE'] = SUMMARY_LANGUAGE



# MongoDB connection config
MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB_NAME = "askthws_scraper"
MONGO_USER = os.getenv("MONGO_USER", "scraper")
MONGO_PASS = os.getenv("MONGO_PASS", "password")
MONGO_PAGES_COLLECTION = "pages"
MONGO_FILES_COLLECTION = "files"
MONGO_EXTRACTED_CONTENT_COLLECTION = "extracted_content"
MONGO_VECTOR_COLLECTION = "vectors"
MONGO_VECTOR_INDEX_NAME = "vector_index"

# Embedding model settings
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DEVICE = "cuda"
EMBEDDING_BATCH_SIZE = 2048
EMBEDDING_CONCURRENCY = 28  # Controls number of concurrent embedding jobs

# LLM configuration (e.g., for Ollama server)
OLLAMA_MODEL_NAME = "mixtral"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_NUM_CTX = 16384
OLLAMA_NUM_PREDICT = 4096


