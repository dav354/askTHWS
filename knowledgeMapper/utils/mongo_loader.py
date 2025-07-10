import os
import sys
import logging
import concurrent.futures
from typing import List, Dict, Any, Tuple

from .db_connector import get_db_connection

async def load_documents_from_mongo() -> Tuple[List[Document], Dict[str, int]]:
    """
    Connects to MongoDB and performs an EFFICIENT HYBRID data load.

    Returns:
        A tuple containing:
        - A list of all processed Document objects.
        - A dictionary with statistics about the loaded documents.
    """
    client, db, fs = await get_db_connection()
    final_docs = []
    stats = {"from_cache": 0, "live_processed": 0}

    lang_filter = {}
    if config.LANGUAGE != "all":
        log.info(f"Filtering all queries for language: '{config.LANGUAGE}'")
        lang_filter = {"lang": config.LANGUAGE}

    # --- 1. Load Pre-processed PDFs from Cache ---
    log.info(
        f"Loading pre-processed PDF data from '{config.MONGO_EXTRACTED_CONTENT_COLLECTION}'..."
    )
    extracted_collection = db[config.MONGO_EXTRACTED_CONTENT_COLLECTION]
    pdf_filter = {}
    if config.LANGUAGE != "all":
        pdf_filter = {"source_metadata.lang": config.LANGUAGE}

    for doc_data in extracted_collection.find(pdf_filter):
        metadata = doc_data.get("source_metadata", {})
        metadata["url"] = doc_data.get("source_url")
        doc = Document(page_content=doc_data.get("extracted_text", ""), metadata=metadata)
        final_docs.append(doc)

    stats["from_cache"] = len(final_docs)
    log.info(f"Loaded {stats['from_cache']} preprocessed PDF documents.")

    # --- 2. Load Raw HTML and iCal for Processing ---
    log.info("Fetching raw HTML and iCal documents...")
    html_docs_raw = list(db[config.MONGO_PAGES_COLLECTION].find(lang_filter))
    ical_filter = {"type": "ical", **lang_filter}
    ical_docs_raw = list(db[config.MONGO_FILES_COLLECTION].find(ical_filter))

    docs_to_process_live = []
    for doc in html_docs_raw:
        docs_to_process_live.append(
            {
                "page_content": doc.get("text", ""),
                "metadata": {
                    "type": "html",
                    "url": doc.get("url"),
                    "lang": doc.get("lang"),
                    "title": doc.get("title"),
                },
            }
        )
    for doc in ical_docs_raw:
        ical_bytes = (
            fs.get(doc["gridfs_id"]).read() if doc.get("gridfs_id") else doc.get("file_content")
        )
        if ical_bytes:
            docs_to_process_live.append(
                {
                    "ical_bytes": ical_bytes,
                    "metadata": {
                        "type": "ical",
                        "url": doc.get("url"),
                        "lang": doc.get("lang"),
                        "title": doc.get("title"),
                    },
                }
            )
    client.close()

    # --- 3. Process Raw Docs in Parallel ---
    if docs_to_process_live:
        log.info(f"Processing {len(docs_to_process_live)} HTML/iCal documents in parallel...")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=os.cpu_count(), initializer=init_worker
        ) as executor:
            live_results = executor.map(process_document_content, docs_to_process_live)
            processed_live_docs = [doc for doc in live_results if doc is not None]
            final_docs.extend(processed_live_docs)
            stats["live_processed"] = len(processed_live_docs)  # Record the count
            log.info(f"Successfully processed {stats['live_processed']} HTML/iCal documents.")

    log.info(f"Total documents loaded and ready for indexing: {len(final_docs)}")

    return final_docs, stats
