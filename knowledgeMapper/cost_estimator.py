import os
import sys
import logging
import concurrent.futures
from typing import List

import tiktoken
from pymongo import MongoClient
from gridfs import GridFS
from rich.console import Console
from rich.table import Table
from tqdm import tqdm
from dotenv import load_dotenv

from .utils.data_processor import process_document_content, init_worker

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "scraper")
MONGO_PASS = os.getenv("MONGO_PASS", "password")
MONGO_DB_NAME = "askthws_scraper"

# Tokenizer model (cl100k_base is used by GPT-3.5/4 and many others)
TOKENIZER_MODEL = "cl100k_base"

# Model pricing (as of June 2025)
# Prices are per 1,000,000 (1M) tokens in US Dollars
MODEL_PRICING = {
    "Embedding": {
        "OpenAI text-embedding-3-large": 0.13,
        "OpenAI text-embedding-3-small": 0.02,
    },
    "Generation (Input/Prompt)": {
        "OpenAI GPT-4o Mini": 0.15,
        "OpenAI GPT-4o": 5.00,
        "Anthropic Claude 3.5 Sonnet": 3.00,
        "Google Gemini 1.5 Flash": 0.35,
        "Google Gemini 1.5 Pro": 3.50,
    },
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


from .utils.db_connector import get_db_connection

async def load_and_process_documents() -> List[str]:
    """
    Connects to MongoDB, loads all documents, and processes them into plain text,
    just like the main pipeline.
    """
    log.info("Connecting to MongoDB...")
    client, db, fs = await get_db_connection()
    log.info("Successfully connected to MongoDB.")

    log.info("Loading document references...")
    pages_docs = list(db["pages"].find({}, {"text": 1, "url": 1, "type": 1}))
    files_docs = list(
        db["files"].find({}, {"gridfs_id": 1, "file_content": 1, "url": 1, "type": 1})
    )
    all_docs_raw = pages_docs + files_docs
    log.info(f"{len(all_docs_raw)} document references found.")

    docs_to_process = []
    for doc in tqdm(all_docs_raw, desc="Preparing documents"):
        metadata = {"url": doc.get("url"), "type": doc.get("type")}
        doc_content = {"metadata": metadata}

        if "text" in doc:
            doc_content["page_content"] = doc["text"]
        elif "gridfs_id" in doc:
            try:
                gridfs_file = fs.get(doc["gridfs_id"])
                # Key for your data processor to find the bytes
                doc_content["pdf_bytes"] = gridfs_file.read()
            except Exception as e:
                log.warning(f"Could not load GridFS file for URL {doc.get('url')}: {e}")
                continue
        elif "file_content" in doc:  # Handles embedded files
            # Key for your data processor to find the bytes
            doc_content["pdf_bytes"] = doc["file_content"]

        docs_to_process.append(doc_content)

    client.close()

    log.info("Processing documents into text (this may take a while)...")
    processed_texts = []
    with concurrent.futures.ProcessPoolExecutor(initializer=init_worker) as executor:
        results = list(
            tqdm(
                executor.map(process_document_content, docs_to_process),
                total=len(docs_to_process),
                desc="Processing content",
            )
        )
        for doc in results:
            if doc and doc.page_content:
                processed_texts.append(doc.page_content)

    return processed_texts


def calculate_costs(total_tokens: int):
    """Calculates the costs and prints a formatted table."""
    console = Console()
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title="\nEstimated Costs for Processing the Entire Dataset",
    )
    table.add_column("Category", style="dim", width=25)
    table.add_column("Model")
    table.add_column("Estimated Cost (USD)")

    total_tokens_in_millions = total_tokens / 1_000_000

    # Embedding costs
    for model, price_per_million in MODEL_PRICING["Embedding"].items():
        cost = total_tokens_in_millions * price_per_million
        table.add_row("Embedding", model, f"${cost:.4f}")

    table.add_section()

    # Generation costs (as input)
    for model, price_per_million in MODEL_PRICING["Generation (Input/Prompt)"].items():
        cost = total_tokens_in_millions * price_per_million
        table.add_row("Generation (as context)", model, f"${cost:.4f}")

    console.print(table)
    console.print(
        "\n[dim]Note: 'Generation' costs assume the entire text is used as input (context) for a request. Actual costs will depend on usage.[/dim]"
    )


async def main():
    """Main function of the script."""
    log.info("Starting the Cost Estimation Tool...")

    # 1. Load and process documents
    all_texts = await load_and_process_documents()
    if not all_texts:
        log.warning("No text content found to process.")
        return

    log.info(f"{len(all_texts)} documents successfully processed into text.")

    # 2. Count tokens
    try:
        tokenizer = tiktoken.get_encoding(TOKENIZER_MODEL)
    except Exception:
        tokenizer = tiktoken.encoding_for_model("gpt-4")  # Fallback

    log.info("Counting tokens for the entire dataset...")
    total_tokens = sum(len(tokenizer.encode(text)) for text in tqdm(all_texts, desc="Tokenizing"))

    log.info(f"✅ Total Tokens Estimated: {total_tokens:,}")

    # 3. Calculate and display costs
    calculate_costs(total_tokens)


if __name__ == "__main__":
    asyncio.run(main())
