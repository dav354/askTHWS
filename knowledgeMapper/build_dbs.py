import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import asyncio
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import config
from langchain.docstore.document import Document
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from utils.chunker import create_structured_chunks
from utils.debug_utils import log_config_summary
from utils.local_models import embedding_func
from utils.mongo_loader import load_documents_from_mongo
from utils.mongo_vector_store import MongoVectorStore
from utils.progress_bar import EstimatedTimeRemainingColumn
from utils.subdomain_utils import get_sanitized_subdomain

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
log = logging.getLogger(__name__)


async def build_vector_store(docs_to_process: List[Document]):
    """Builds a vector store from the processed documents."""
    log.info(f"--- Building Vector Store from {len(docs_to_process)} documents ---")
    try:
        vector_store = MongoVectorStore(
            db_name=config.MONGO_DB_NAME,
            collection_name=config.MONGO_VECTOR_COLLECTION,
            vector_index_name=config.MONGO_VECTOR_INDEX_NAME,
        )
        await vector_store.ainit()
        # Ensure the collection exists before creating the index
        try:
            await vector_store.db.create_collection(config.MONGO_VECTOR_COLLECTION)
            log.info(f"Collection '{config.MONGO_VECTOR_COLLECTION}' created.")
        except Exception as e:
            log.info(
                f"Collection '{config.MONGO_VECTOR_COLLECTION}' already exists or could not be created: {e}"
            )

        await vector_store.create_vector_index()

        log.info("Applying structured chunking...")
        structured_chunks = create_structured_chunks(docs_to_process)
        chunk_count = len(structured_chunks)
        log.info(f"Split documents into {chunk_count} structured chunks.")

        log.info("Generating embeddings and adding to vector store...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[green]Processing chunks..."),
            BarColumn(),
            TextColumn("[bold blue]{task.completed}/{task.total} chunks"),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            EstimatedTimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Embedding", total=chunk_count)
            for i, chunk in enumerate(structured_chunks):
                embedding = (await embedding_func([chunk.page_content]))[0]
                document_to_insert = {
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata,
                    "vector": embedding,
                }
                await vector_store.collection.insert_one(document_to_insert)
                progress.update(task, advance=1)

        log.info(f"Added {chunk_count} documents to the vector store.")

        log.info("[bold green]✅ Vector Store built successfully.[/bold green]")
        return True
    except Exception as e:
        log.exception(f"❌ FAILED to build vector store: {e}")
        return False
    finally:
        if "vector_store" in locals() and vector_store:
            await vector_store.close()


async def main(args):
    """
    Main entrypoint: Loads documents, filters them, displays the stats for the
    filtered set, and builds the vector store.
    """
    log_config_summary()

    all_documents, _ = await load_documents_from_mongo()

    if not all_documents:
        log.warning("No documents loaded from MongoDB. Aborting.")
        return

    docs_to_process = []
    if args.subdomain:
        log.info(f"Filtering for subdomains: {args.subdomain}")
        selected_subdomains = set(args.subdomain)
        for doc in all_documents:
            url = doc.metadata.get("url")
            subdomain = get_sanitized_subdomain(url)
            if subdomain in selected_subdomains:
                docs_to_process.append(doc)
        if not docs_to_process:
            log.error("None of the specified subdomains were found. Aborting.")
            return
    else:
        log.info("No subdomain filter provided. Using all loaded documents.")
        docs_to_process = all_documents

    log.info("Documents to be processed in this build:")

    subdomain_counts = defaultdict(int)
    for doc in docs_to_process:
        subdomain = get_sanitized_subdomain(doc.metadata.get("url"))
        subdomain_counts[subdomain] += 1

    for subdomain, count in sorted(subdomain_counts.items()):
        log.info(f"  - {subdomain}: {count} documents")

    log.info(f"Total to Process: {len(docs_to_process)} documents")

    success = await build_vector_store(docs_to_process)

    if success:
        log.info("✅ Build process completed successfully.")
    else:
        log.warning("❌ Build process failed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a RAG Vector Store from MongoDB content.")
    parser.add_argument(
        "--subdomain",
        action="append",
        help="Build vector store using only documents from one or more specific subdomains.",
    )
    args = parser.parse_args()
    asyncio.run(main(args))
