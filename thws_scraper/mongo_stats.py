#!/usr/bin/env python3

import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo import errors as pymongo_errors


# --- Configuration ---
def load_config():
    """Loads configuration from environment variables or .env file."""
    load_dotenv()
    config = {
        "mongo_user": os.getenv("MONGO_USER", "scraper"),
        "mongo_pass": os.getenv("MONGO_PASS", "password"),
        "mongo_db_name": os.getenv("MONGO_DB_NAME", os.getenv("MONGO_DB", "askthws_scraper")),
        "mongo_host": os.getenv("MONGO_HOST", "localhost"),
        "mongo_port": int(os.getenv("MONGO_PORT", 27017)),
        "mongo_auth_db": os.getenv("MONGO_AUTH_DB", "admin"),
        "pages_collection": os.getenv("MONGO_PAGES_COLLECTION", "pages"),
        "files_collection": os.getenv("MONGO_FILES_COLLECTION", "files"),
    }
    return config


# --- Helper Functions ---
def get_db_connection(config):
    """Establishes and returns a MongoDB database connection."""
    mongo_uri = (
        f"mongodb://{config['mongo_user']}:{config['mongo_pass']}@"
        f"{config['mongo_host']}:{config['mongo_port']}/"
        f"?authSource={config['mongo_auth_db']}"
    )
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth, good for checking connection.
        client.admin.command("ismaster")
        db = client[config["mongo_db_name"]]
        print(
            f"Successfully connected to MongoDB: {config['mongo_host']}:{config['mongo_port']}, DB: {config['mongo_db_name']}"
        )  # noqa 501
        return db
    except pymongo_errors.ConnectionFailure as e:
        print(
            f"Error: Could not connect to MongoDB at {config['mongo_host']}:{config['mongo_port']}",
            file=sys.stderr,
        )
        print(f"Details: {e}", file=sys.stderr)
        print(
            f"Attempted URI: mongodb://<USER>:<PASS>@{config['mongo_host']}:{config['mongo_port']}/?authSource={config['mongo_auth_db']}",  # noqa 501
            file=sys.stderr,
        )
        sys.exit(1)
    except pymongo_errors.OperationFailure as e:  # Handles auth errors
        print("Error: MongoDB authentication failed or operation denied.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print(
            f"Please check credentials and permissions for user '{config['mongo_user']}' on authSource '{config['mongo_auth_db']}'.",  # noqa 501
            file=sys.stderr,
        )
        sys.exit(1)


def print_table_header(title):
    print(f"\n--- {title} ---")


def format_bytes(bytes_val):
    """Formats bytes into a human-readable string (KB, MB, GB)."""
    if not isinstance(bytes_val, (int, float)):
        bytes_val = 0
    if bytes_val < 0:
        bytes_val = 0  # Ensure non-negative

    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024**2:
        return f"{bytes_val/1024:.2f} KB"
    elif bytes_val < 1024**3:
        return f"{bytes_val/(1024**2):.2f} MB"
    else:
        return f"{bytes_val/(1024**3):.2f} GB"


# --- Statistics Functions ---


def get_type_counts(db, pages_coll_name, files_coll_name):
    print_table_header("Item Types Count")
    type_counts = Counter()
    try:
        for doc in db[pages_coll_name].find({}, {"type": 1}):
            type_counts[doc.get("type", "N/A")] += 1
        for doc in db[files_coll_name].find({}, {"type": 1}):
            type_counts[doc.get("type", "N/A")] += 1
    except pymongo_errors.PyMongoError as e:
        print(f" Error querying type counts: {e}", file=sys.stderr)
        return

    print(f"{'Type':<15} | {'Count':>7}")
    print(f"{'-'*15}-+-{'-'*7}")
    for item_type, count in sorted(type_counts.items()):
        print(f"{item_type:<15} | {count:>7}")


def get_language_counts(db, pages_coll_name, files_coll_name):
    print_table_header("Detected Languages Count")
    lang_counts = Counter()
    try:
        for doc in db[pages_coll_name].find({}, {"lang": 1}):
            lang_counts[doc.get("lang", "N/A")] += 1
        for doc in db[files_coll_name].find({}, {"lang": 1}):
            lang_counts[doc.get("lang", "N/A")] += 1
    except pymongo_errors.PyMongoError as e:
        print(f" Error querying language counts: {e}", file=sys.stderr)
        return

    print(f"{'Language':<15} | {'Count':>7}")
    print(f"{'-'*15}-+-{'-'*7}")
    # Sort by count descending, then by language ascending
    for lang, count in sorted(lang_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{lang:<15} | {count:>7}")


def get_scraped_items_per_day(db, pages_coll_name, files_coll_name):
    print_table_header("Scraped Items per Day (UTC)")
    daily_counts = Counter()

    pipeline = [
        {
            "$match": {"date_scraped": {"$ne": None, "$exists": True}}
        },  # Ensure field exists and is not null
        {
            "$project": {
                "dayScraped": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        # $toDate handles ISO strings and existing BSON Date objects
                        "date": {"$toDate": "$date_scraped"},
                    }
                }
            }
        },
        {"$group": {"_id": "$dayScraped", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},  # Sort by date ascending
    ]
    try:
        for result in db[pages_coll_name].aggregate(pipeline):
            daily_counts[result["_id"]] += result["count"]
        for result in db[files_coll_name].aggregate(pipeline):
            daily_counts[result["_id"]] += result["count"]
    except pymongo_errors.PyMongoError as e:
        print(f" Error querying scraped items per day: {e}", file=sys.stderr)
        return

    print(f"{'Date (UTC)':<15} | {'Count':>7}")
    print(f"{'-'*15}-+-{'-'*7}")
    for day, count in sorted(daily_counts.items()):  # Python sort for final combined dict
        print(f"{day:<15} | {count:>7}")


def get_http_code_counts(db, pages_coll_name, files_coll_name):
    print_table_header("HTTP Status Codes Count")
    status_counts = Counter()
    try:
        for doc in db[pages_coll_name].find({}, {"status": 1}):
            status_counts[str(doc.get("status", "N/A"))] += 1  # Ensure status is string for key
        for doc in db[files_coll_name].find({}, {"status": 1}):
            status_counts[str(doc.get("status", "N/A"))] += 1
    except pymongo_errors.PyMongoError as e:
        print(f" Error querying HTTP status codes: {e}", file=sys.stderr)
        return

    print(f"{'HTTP Status':<15} | {'Count':>7}")
    print(f"{'-'*15}-+-{'-'*7}")
    for status, count in sorted(status_counts.items(), key=lambda item: item[0]):
        print(f"{status:<15} | {count:>7}")


def get_size_stats(db, pages_coll_name, files_coll_name):
    print_table_header("Size Statistics")

    total_file_bytes = 0
    total_file_count = 0
    total_html_chars = 0
    total_html_count = 0

    try:
        # Totals from files collection
        files_total_result = list(
            db[files_coll_name].aggregate(
                [
                    {
                        "$group": {
                            "_id": None,
                            "totalSize": {"$sum": "$file_size"},
                            "totalCount": {"$sum": 1},
                        }
                    }
                ]
            )
        )
        if files_total_result:
            total_file_bytes = files_total_result[0].get("totalSize", 0)
            total_file_count = files_total_result[0].get("totalCount", 0)

        # Totals from pages collection (HTML text length)
        pages_total_result = list(
            db[pages_coll_name].aggregate(
                [
                    {
                        "$match": {"text": {"$type": "string"}}
                    },  # Ensure text is a string for $strLenCP
                    {"$project": {"textSize": {"$strLenCP": "$text"}}},
                    {
                        "$group": {
                            "_id": None,
                            "totalCharSize": {"$sum": "$textSize"},
                            "totalCount": {"$sum": 1},
                        }
                    },
                ]
            )
        )
        if pages_total_result:
            total_html_chars = pages_total_result[0].get("totalCharSize", 0)
            total_html_count = pages_total_result[0].get("totalCount", 0)
    except pymongo_errors.PyMongoError as e:
        print(f" Error querying total sizes: {e}", file=sys.stderr)
        # Continue to print what might have been collected or defaults

    print("Overall Size:")
    print(
        f"  Total Bytes (files coll.): {format_bytes(total_file_bytes)} ({total_file_count} items)"
    )
    print(f"  Total Chars (pages.text):  {total_html_chars:,} chars ({total_html_count} items)")
    print("\nAverage Size per Type:")
    print(f"{'Type':<10} | {'Count':<10} | {'Avg Size':<17} | {'Collection':<12}")
    print(f"{'-'*10}-+-{'-'*10}-+-{'-'*17}-+-{'-'*12}")

    try:
        # Average size per type for files
        for result in db[files_coll_name].aggregate(
            [{"$group": {"_id": "$type", "avgSize": {"$avg": "$file_size"}, "count": {"$sum": 1}}}]
        ):
            avg_size = int(result.get("avgSize", 0))
            print(
                f"{result.get('_id', 'N/A'):<10} | {result.get('count', 0):<10} | {format_bytes(avg_size):<17} | {'files':<12}"
            )  # noqa 501

        # Average char length per type for pages
        for result in db[pages_coll_name].aggregate(
            [
                {"$match": {"text": {"$type": "string"}}},
                {"$project": {"type": "$type", "textSize": {"$strLenCP": "$text"}}},
                {
                    "$group": {
                        "_id": "$type",
                        "avgCharSize": {"$avg": "$textSize"},
                        "count": {"$sum": 1},
                    }
                },
            ]
        ):
            avg_chars = int(result.get("avgCharSize", 0))
            print(
                f"{result.get('_id', 'N/A'):<10} | {result.get('count', 0):<10} | {f'{avg_chars:,} chars':<17} | {'pages (text)':<12}"
            )  # noqa 501
    except pymongo_errors.PyMongoError as e:
        print(f" Error querying average sizes: {e}", file=sys.stderr)


# --- NEW Statistics Functions ---


def get_date_updated_stats(db, pages_coll_name):
    print_table_header("HTML Content Freshness (date_updated from page)")

    items_with_date_updated = 0
    items_without_date_updated = 0
    date_updated_years = Counter()
    total_age_seconds = 0.0
    items_with_age_info = 0

    try:
        # date_updated is primarily relevant for HTML pages
        for doc in db[pages_coll_name].find(
            {"type": "html"}, {"date_updated": 1, "date_scraped": 1}
        ):
            date_updated_val = doc.get(
                "date_updated"
            )  # This should be a datetime object if stored correctly by pymongo
            date_scraped_val = doc.get("date_scraped")  # This too

            if date_updated_val:
                # Ensure it's a datetime object
                if isinstance(date_updated_val, str):
                    try:
                        date_updated_val = datetime.fromisoformat(
                            date_updated_val.replace("Z", "+00:00")
                        )
                    except ValueError:
                        items_without_date_updated += 1  # Treat unparseable string as missing
                        continue

                # Ensure timezone aware (assume UTC if naive)
                if date_updated_val.tzinfo is None:
                    date_updated_val = date_updated_val.replace(tzinfo=timezone.utc)

                items_with_date_updated += 1
                date_updated_years[date_updated_val.year] += 1

                if date_scraped_val:
                    if isinstance(date_scraped_val, str):
                        try:
                            date_scraped_val = datetime.fromisoformat(
                                date_scraped_val.replace("Z", "+00:00")
                            )
                        except ValueError:
                            continue  # Skip age calculation if scraped_date is bad

                    if date_scraped_val.tzinfo is None:
                        date_scraped_val = date_scraped_val.replace(tzinfo=timezone.utc)

                    if date_scraped_val > date_updated_val:
                        total_age_seconds += (date_scraped_val - date_updated_val).total_seconds()
                        items_with_age_info += 1
            else:
                items_without_date_updated += 1

        total_html_pages = items_with_date_updated + items_without_date_updated
        if total_html_pages == 0:
            print("  No HTML pages found to analyze for date_updated.")
            return

        print(f"  Total HTML Pages Analyzed: {total_html_pages}")
        perc_with_date = (
            (items_with_date_updated / total_html_pages * 100) if total_html_pages > 0 else 0
        )
        print(f"  Pages with 'date_updated': {items_with_date_updated} ({perc_with_date:.2f}%)")
        print(f"  Pages without 'date_updated' or unparseable: {items_without_date_updated}")

        if items_with_age_info > 0:
            avg_age_days = (total_age_seconds / items_with_age_info) / (24 * 3600)
            print(
                f"  Average content age at scrape time: {avg_age_days:.2f} days (for pages with valid date_updated & date_scraped)"
            )  # noqa 501
        else:
            print(
                "  Average content age: N/A (no valid date_updated entries or date_scraped for comparison)"
            )  # noqa 501

        if date_updated_years:
            print("\n  Distribution of 'date_updated' by Year:")
            print(f"    {'Year':<10} | {'Count':>7}")
            print(f"    {'-'*10}-+-{'-'*7}")
            for year, count in sorted(
                date_updated_years.items(), key=lambda item: item[0], reverse=True
            ):
                print(f"    {year:<10} | {count:>7}")

    except pymongo_errors.PyMongoError as e:
        print(f" Error querying for date_updated stats: {e}", file=sys.stderr)


def get_metadata_completeness_stats(db, pages_coll_name):
    print_table_header("HTML Metadata Completeness")

    total_html_pages = 0
    with_meta_desc = 0
    with_og_title = 0
    with_og_desc = 0
    og_type_counts = Counter()

    try:
        query_filter = {"type": "html"}
        projection = {"metadata_extracted": 1}  # Only fetch the field we need

        total_html_pages = db[pages_coll_name].count_documents(query_filter)
        if total_html_pages == 0:
            print("  No HTML pages found to analyze for metadata.")
            return

        for doc in db[pages_coll_name].find(query_filter, projection):
            metadata = doc.get("metadata_extracted", {})  # Ensure metadata_extracted exists
            if isinstance(metadata, dict):  # Check if it's a dictionary as expected
                if metadata.get("meta_description"):
                    with_meta_desc += 1
                if metadata.get("og_title"):
                    with_og_title += 1
                if metadata.get("og_description"):
                    with_og_desc += 1
                og_type = metadata.get("og_type")
                if og_type:
                    og_type_counts[og_type] += 1

        print(f"  Total HTML Pages Analyzed: {total_html_pages}")

        def print_perc(label, count, total):
            perc = (count / total * 100) if total > 0 else 0
            print(f"  {label:<35}: {count:>7} ({perc:>6.2f}%)")

        print_perc("Pages with Meta Description", with_meta_desc, total_html_pages)
        print_perc("Pages with OpenGraph Title", with_og_title, total_html_pages)
        print_perc("Pages with OpenGraph Description", with_og_desc, total_html_pages)

        if og_type_counts:
            print("\n  Distribution of 'og:type':")
            print(f"    {'OG Type':<25} | {'Count':>7}")
            print(f"    {'-'*25}-+-{'-'*7}")
            for og_type, count in sorted(
                og_type_counts.items(), key=lambda item: (-item[1], item[0])
            ):
                print(f"    {og_type:<25} | {count:>7}")
        else:
            print("  No OpenGraph types found.")

    except pymongo_errors.PyMongoError as e:
        print(f" Error querying for metadata completeness stats: {e}", file=sys.stderr)


def get_text_length_distribution_stats(db, pages_coll_name):
    print_table_header("HTML Text Length Distribution (Cleaned Content)")

    buckets_def = [
        (0, "0 chars"),  # Exact 0
        (1, "1-100 chars"),  # 1 to 100
        (101, "101-500 chars"),  # 101 to 500
        (501, "501-2000 chars"),  # 501 to 2000
        (2001, "2001-5000 chars"),  # 2001 to 5000
        (5001, "5001+ chars"),  # 5001 and above
    ]

    # MongoDB $bucket boundaries are [lower_bound, upper_bound).
    mongo_boundaries = [b[0] for b in buckets_def]
    mongo_boundaries.append(math.inf)  # Upper bound for the last bucket

    pipeline = [
        {"$match": {"type": "html", "text": {"$exists": True}}},  # Text field exists
        {
            "$project": {
                "textLength": {"$cond": [{"$eq": ["$text", None]}, 0, {"$strLenCP": "$text"}]}
            }
        },  # Handle null text
        {
            "$bucket": {
                "groupBy": "$textLength",
                "boundaries": mongo_boundaries,
                "default": "ErrorBucket",
                "output": {"count": {"$sum": 1}},
            }
        },
    ]

    try:
        results = list(db[pages_coll_name].aggregate(pipeline))
        if not results:
            print("  No HTML pages with text content found for length analysis.")
            return

        print(f"  {'Length Bucket':<20} | {'Count':>7}")
        print(f"  {'-'*20}-+-{'-'*7}")

        # Map MongoDB bucket _id (lower bound) to our labels
        # Create a lookup from lower bound to label
        label_map = {b[0]: b[1] for b in buckets_def}

        # Sort results by the numeric _id (lower bound of bucket)
        sorted_results = sorted(
            results, key=lambda x: x["_id"] if isinstance(x["_id"], (int, float)) else -1
        )

        for res_bucket in sorted_results:
            bucket_id = res_bucket["_id"]
            label = label_map.get(bucket_id, str(bucket_id))  # Use label from map
            if bucket_id == "ErrorBucket":
                label = "Other (Error in bucketing)"
            print(f"  {label:<20} | {res_bucket.get('count', 0):>7}")

    except pymongo_errors.PyMongoError as e:
        print(f" Error querying for text length distribution: {e}", file=sys.stderr)


# --- Main Script ---
if __name__ == "__main__":
    config = load_config()
    db = get_db_connection(config)

    print(f"\nMongoDB Scraper Statistics for database: {config['mongo_db_name']}")
    print("======================================================")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")  # Added timezone

    # Existing stats
    get_type_counts(db, config["pages_collection"], config["files_collection"])
    get_language_counts(db, config["pages_collection"], config["files_collection"])
    get_scraped_items_per_day(db, config["pages_collection"], config["files_collection"])
    get_http_code_counts(db, config["pages_collection"], config["files_collection"])
    get_size_stats(db, config["pages_collection"], config["files_collection"])

    # New stats
    get_date_updated_stats(db, config["pages_collection"])
    get_metadata_completeness_stats(db, config["pages_collection"])
    get_text_length_distribution_stats(db, config["pages_collection"])

    print("\n--- End of Report ---")
