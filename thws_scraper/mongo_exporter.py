import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import gridfs
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from tqdm import tqdm

# --- Configuration ---
load_dotenv()
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "scraper")
MONGO_PASS = os.getenv("MONGO_PASS", "password")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "askthws_scraper")
PAGES_COLLECTION = "pages"
FILES_COLLECTION = "files"
DEFAULT_OUTPUT_DIR = Path("./mongo_export_output")
JSON_SUBDIR = "json_data"
FILES_SUBDIR = "downloaded_files"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class MongoEncoder(json.JSONEncoder):
    """
    A special JSON encoder that can handle MongoDB's ObjectId, datetime,
    and bytes objects.
    """

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return f"<binary data of size {len(obj)} bytes>"
        return json.JSONEncoder.default(self, obj)


def export_collections_to_json(db, output_dir: Path):
    """Exports the 'pages' and 'files' collections into separate JSON files."""
    json_output_path = output_dir / JSON_SUBDIR
    json_output_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Exporting JSON data to: {json_output_path}")

    # Export the pages collection
    logging.info(f"Reading '{PAGES_COLLECTION}' collection...")
    pages_collection = db[PAGES_COLLECTION]
    pages_docs = list(pages_collection.find())
    pages_filepath = json_output_path / f"{PAGES_COLLECTION}.json"
    with open(pages_filepath, "w", encoding="utf-8") as f:
        json.dump(pages_docs, f, cls=MongoEncoder, indent=2, ensure_ascii=False)
    logging.info(
        f"✅ Saved {len(pages_docs)} documents from '{PAGES_COLLECTION}' to {pages_filepath}."
    )

    # Export the files collection metadata
    logging.info(f"Reading '{FILES_COLLECTION}' collection (metadata only)...")
    files_collection = db[FILES_COLLECTION]
    files_docs = list(files_collection.find())
    files_filepath = json_output_path / f"{FILES_COLLECTION}_metadata.json"
    with open(files_filepath, "w", encoding="utf-8") as f:
        json.dump(files_docs, f, cls=MongoEncoder, indent=2, ensure_ascii=False)
    logging.info(
        f"✅ Saved {len(files_docs)} document metadata records from '{FILES_COLLECTION}' to {files_filepath}."
    )


def export_gridfs_files(db, output_dir: Path):
    """Downloads all files from GridFS and saves them to a folder."""
    files_output_path = output_dir / FILES_SUBDIR
    files_output_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Downloading files from GridFS to: {files_output_path}")

    fs = gridfs.GridFS(db)
    files_to_download = list(db[FILES_COLLECTION].find({"gridfs_id": {"$exists": True}}))
    if not files_to_download:
        logging.warning(
            "No files with 'gridfs_id' found in the files collection. Skipping GridFS download."
        )
        return

    for doc in tqdm(files_to_download, desc="Downloading GridFS files"):
        gridfs_id = doc.get("gridfs_id")
        try:
            gridfs_file = fs.get(gridfs_id)
            fallback_filename = Path(doc.get("url", str(gridfs_id))).name
            filename = gridfs_file.filename or fallback_filename
            sanitized_filename = "".join(
                c for c in filename if c.isalnum() or c in (".", "_", "-")
            ).strip()
            if not sanitized_filename:
                sanitized_filename = str(gridfs_id)
            output_filepath = files_output_path / sanitized_filename
            with open(output_filepath, "wb") as f:
                f.write(gridfs_file.read())
        except gridfs.errors.NoFile:
            logging.error(
                f"File with gridfs_id {gridfs_id} (URL: {doc.get('url')}) not found in GridFS."
            )
        except Exception as e:
            logging.error(f"Error downloading GridFS file {gridfs_id}: {e}")
    logging.info(f"✅ Download of {len(files_to_download)} GridFS files complete.")


# --- NEW FUNCTION ---
def export_embedded_files(db, output_dir: Path):
    """
    Finds documents with binary data in the 'file_content' field and saves them as files.
    """
    files_output_path = output_dir / FILES_SUBDIR
    files_output_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Exporting embedded files from 'file_content' field to: {files_output_path}")

    # Find documents where 'file_content' exists and is of binary type
    query = {"file_content": {"$exists": True, "$type": "binData"}}
    embedded_files_to_export = list(db[FILES_COLLECTION].find(query))

    if not embedded_files_to_export:
        logging.warning("No documents with embedded 'file_content' found. Skipping.")
        return

    for doc in tqdm(embedded_files_to_export, desc="Exporting embedded files"):
        file_bytes = doc.get("file_content")
        if not isinstance(file_bytes, bytes) or not file_bytes:
            continue

        try:
            # Use the document's URL to determine a filename
            filename = Path(doc.get("url", str(doc.get("_id")))).name
            if not filename:  # Fallback if URL is a directory
                filename = str(doc.get("_id"))

            # Sanitize the filename
            sanitized_filename = "".join(
                c for c in filename if c.isalnum() or c in (".", "_", "-")
            ).strip()
            if not sanitized_filename:
                sanitized_filename = str(doc.get("_id"))

            output_filepath = files_output_path / sanitized_filename

            with open(output_filepath, "wb") as f:
                f.write(file_bytes)

        except Exception as e:
            logging.error(f"Error exporting embedded file from doc_id {doc.get('_id')}: {e}")

    logging.info(f"✅ Export of {len(embedded_files_to_export)} embedded files complete.")


def main():
    """Main function of the script."""
    logging.info("Starting MongoDB Export Tool...")

    required_vars = {
        "MONGO_USER": MONGO_USER,
        "MONGO_PASS": MONGO_PASS,
        "MONGO_DB_NAME": MONGO_DB_NAME,
    }
    for var_name, value in required_vars.items():
        if not value:
            logging.error(f"Configuration Error: Environment variable '{var_name}' is not set.")
            logging.error(
                "Please create or check your .env file and ensure all required variables have a value."
            )
            sys.exit(1)

    mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"

    client = None
    try:
        client = MongoClient(mongo_uri)
        db = client[MONGO_DB_NAME]
        db.command("ping")
        logging.info("Successfully connected to MongoDB.")

        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Run all three export steps
        export_collections_to_json(db, DEFAULT_OUTPUT_DIR)
        export_gridfs_files(db, DEFAULT_OUTPUT_DIR)
        export_embedded_files(db, DEFAULT_OUTPUT_DIR)  # <-- Call the new function

        logging.info("🎉 Export completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if client:
            client.close()
            logging.info("MongoDB connection closed.")


if __name__ == "__main__":
    main()
