import logging  # ADDED
from datetime import datetime

from gridfs import GridFS
from gridfs.errors import GridFSError
from itemadapter import ItemAdapter
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from scrapy.exceptions import CloseSpider, DropItem

from .items import RawPageItem

# Get a logger instance for this module (though most logging here uses spider.logger)
module_logger = logging.getLogger(__name__)  # ADDED

MAX_EMBEDDED_FILE_SIZE = 15 * 1024 * 1024  # Mongo max 16mb, so 15 is safe


class MongoPipeline:
    """
    A Scrapy pipeline to store items in MongoDB.
    Handles RawPageItems:
    - 'html' type goes to a 'pages' collection.
    - 'pdf', 'ical' types:
        - Small files are stored directly in the 'files' collection.
        - Large files (content > MAX_EMBEDDED_FILE_SIZE) are stored in GridFS,
          and a reference (gridfs_id) is stored in the 'files' collection.
    """

    def __init__(
        self,
        mongo_host,
        mongo_port,
        mongo_db_name,
        mongo_user,
        mongo_pass,
        pages_collection_name,
        files_collection_name,
    ):
        self.mongo_host = mongo_host
        self.mongo_port = int(mongo_port)
        self.mongo_db_name = mongo_db_name
        self.mongo_user = mongo_user
        self.mongo_pass = mongo_pass
        self.pages_collection_name = pages_collection_name
        self.files_collection_name = files_collection_name

        self.client = None
        self.db = None
        self.fs = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_host=crawler.settings.get("MONGO_HOST"),
            mongo_port=crawler.settings.get("MONGO_PORT"),
            mongo_db_name=crawler.settings.get("MONGO_DB_NAME"),
            mongo_user=crawler.settings.get("MONGO_USER"),
            mongo_pass=crawler.settings.get("MONGO_PASS"),
            pages_collection_name=crawler.settings.get("MONGO_PAGES_COLLECTION", "pages"),
            files_collection_name=crawler.settings.get("MONGO_FILES_COLLECTION", "files"),
        )

    def open_spider(self, spider):
        try:
            if self.mongo_user and self.mongo_pass:
                uri = f"mongodb://{self.mongo_user}:{self.mongo_pass}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db_name}?authSource=admin"  # noqa 501
            else:
                uri = f"mongodb://{self.mongo_host}:{self.mongo_port}/"

            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)  # Added timeout
            self.client.admin.command("ping")  # Verify connection
            self.db = self.client[self.mongo_db_name]
            self.fs = GridFS(self.db)
            spider.logger.info(
                "MongoPipeline: Connected to MongoDB and GridFS initialized",
                extra={
                    "event_type": "mongodb_connected",
                    "pipeline_class": self.__class__.__name__,
                    "mongo_host": self.mongo_host,
                    "mongo_port": self.mongo_port,
                    "mongo_db_name": self.mongo_db_name,
                },
            )

            self.db[self.pages_collection_name].create_index("url", unique=True)
            self.db[self.files_collection_name].create_index("url", unique=True)
            spider.logger.info(
                "MongoPipeline: Ensured indexes on 'url' for collections",
                extra={
                    "event_type": "mongodb_index_ensured",
                    "pipeline_class": self.__class__.__name__,
                    "collections": [self.pages_collection_name, self.files_collection_name],
                },
            )

        except ConnectionFailure as e:
            spider.logger.error(
                "MongoPipeline: MongoDB connection failed at startup",
                extra={
                    "event_type": "mongodb_connection_failure",
                    "pipeline_class": self.__class__.__name__,
                    "mongo_host": self.mongo_host,
                    "mongo_port": self.mongo_port,
                    "error": str(e),
                },
            )
            self.client = None
            self.db = None
            self.fs = None
            raise CloseSpider(f"MongoDB connection failed at startup: {e}")
        except OperationFailure as e:  # Handles auth errors during ping or index creation
            spider.logger.error(
                "MongoPipeline: MongoDB operation failure during setup (e.g., auth, permissions)",
                extra={
                    "event_type": "mongodb_operation_failure_setup",
                    "pipeline_class": self.__class__.__name__,
                    "mongo_host": self.mongo_host,
                    "mongo_port": self.mongo_port,
                    "mongo_db_name": self.mongo_db_name,
                    "error": str(e),
                },
            )
            self.client = None
            self.db = None
            self.fs = None
            raise CloseSpider(f"MongoDB operation failure during setup: {e}")
        except Exception as e:
            spider.logger.error(
                "MongoPipeline: An unexpected error occurred during MongoDB setup",
                extra={
                    "event_type": "mongodb_unexpected_setup_error",
                    "pipeline_class": self.__class__.__name__,
                    "error": str(e),
                    "traceback": (
                        logging.Formatter().formatException(logging.sys.exc_info())
                        if logging.sys
                        else str(e)
                    ),
                },
            )
            self.client = None
            self.db = None
            self.fs = None
            raise CloseSpider(f"MongoDB setup failed due to unexpected error: {e}")

    def close_spider(self, spider):
        if self.client:
            self.client.close()
            spider.logger.info(
                "MongoPipeline: Closed MongoDB connection",
                extra={
                    "event_type": "mongodb_connection_closed",
                    "pipeline_class": self.__class__.__name__,
                },
            )

    def process_item(self, item, spider):
        if self.db is None or self.fs is None:
            spider.logger.error(
                "MongoPipeline: No MongoDB connection or GridFS not initialized, dropping item",
                extra={
                    "event_type": "mongodb_not_initialized_drop",
                    "pipeline_class": self.__class__.__name__,
                    "item_url": item.get("url", "N/A"),
                    "item_type": item.get("type", "N/A"),
                },
            )
            raise DropItem(f"No MongoDB connection/GridFS for item {item.get('url')}")

        if not isinstance(item, RawPageItem):
            return item  # Pass through other item types

        adapter = ItemAdapter(item)
        item_type = adapter.get("type")
        url = adapter.get("url", "N/A_URL")  # Default if URL is missing

        item_dict = {}
        for key, value in adapter.asdict().items():
            if value is not None:
                item_dict[key] = value.isoformat() if isinstance(value, datetime) else value

        if "text" in item_dict and isinstance(item_dict["text"], str):
            item_dict["text"] = item_dict["text"].replace("\x00", "")
        if "title" in item_dict and isinstance(item_dict["title"], str):
            item_dict["title"] = item_dict["title"].replace("\x00", "")

        collection_name = None
        gridfs_id_generated = None  # To log later

        if item_type == "html":
            collection_name = self.pages_collection_name
            if "file_content" in item_dict and not item_dict.get("file_content"):
                del item_dict["file_content"]
        elif item_type in ["pdf", "ical"]:
            collection_name = self.files_collection_name
            original_file_content = item_dict.pop("file_content", None)
            item_dict.pop("gridfs_id", None)  # Remove any pre-existing, we'll manage it

            if "text" in item_dict and not item_dict["text"]:
                del item_dict["text"]

            if original_file_content:
                file_size = len(original_file_content)
                item_dict["file_size"] = file_size

                if file_size > MAX_EMBEDDED_FILE_SIZE:
                    try:
                        # Delete existing GridFS file with the same filename (URL) to ensure update
                        for old_file in self.fs.find({"filename": url}):
                            self.fs.delete(old_file._id)
                            spider.logger.debug(
                                "MongoPipeline: Deleted existing GridFS file version before new PUT",  # noqa 501
                                extra={
                                    "event_type": "gridfs_deleted_old_version",
                                    "pipeline_class": self.__class__.__name__,
                                    "url": url,
                                    "gridfs_id_deleted": str(old_file._id),
                                },
                            )

                        file_metadata_for_gridfs = {
                            "url": url,
                            "type": item_type,
                            "original_title": item_dict.get("title"),
                            "lang": item_dict.get("lang"),
                        }
                        gridfs_id_generated = self.fs.put(
                            original_file_content, filename=url, metadata=file_metadata_for_gridfs
                        )
                        item_dict["gridfs_id"] = (
                            gridfs_id_generated  # Store ObjectId as is, mongo driver handles it
                        )
                        spider.logger.info(  # Changed from debug for better visibility of large file storage # noqa 501
                            "MongoPipeline: Stored large file in GridFS",
                            extra={
                                "event_type": "gridfs_file_stored",
                                "pipeline_class": self.__class__.__name__,
                                "url": url,
                                "file_size": file_size,
                                "gridfs_id": str(gridfs_id_generated),
                            },
                        )
                    except GridFSError as e:
                        spider.logger.error(
                            "MongoPipeline: GridFS error storing large file",
                            extra={
                                "event_type": "gridfs_storage_error",
                                "pipeline_class": self.__class__.__name__,
                                "url": url,
                                "file_size": file_size,
                                "error": str(e),
                            },
                        )
                        raise DropItem(f"GridFS error for {url}: {e}")
                    # Catching generic Exception for GridFS PUT is already in open_spider for setup,
                    # but could be added here too if very specific PUT errors are expected.
                else:  # File is small, embed directly
                    item_dict["file_content"] = original_file_content
                    spider.logger.debug(
                        "MongoPipeline: Embedded small file content directly in document",
                        extra={
                            "event_type": "file_embedded_in_doc",
                            "pipeline_class": self.__class__.__name__,
                            "url": url,
                            "file_size": file_size,
                        },
                    )
            else:  # No original_file_content for PDF/iCAL
                spider.logger.warning(
                    "MongoPipeline: No file_content for binary item type, will be upserted without file data.",
                    extra={
                        "event_type": "file_content_missing_for_binary",
                        "pipeline_class": self.__class__.__name__,
                        "url": url,
                        "item_type": item_type,
                    },
                )
                item_dict["file_size"] = 0
        else:  # Unknown item type
            spider.logger.warning(
                "MongoPipeline: Unknown item type, passing through.",
                extra={
                    "event_type": "unknown_item_type_pipeline",
                    "pipeline_class": self.__class__.__name__,
                    "item_url": url,
                    "item_type": item_type,
                },
            )
            return item  # Pass through unknown item types

        if collection_name:
            try:
                self.db[collection_name].update_one({"url": url}, {"$set": item_dict}, upsert=True)
                log_extras_upsert = {
                    "event_type": "mongodb_item_upserted",
                    "pipeline_class": self.__class__.__name__,
                    "url": url,
                    "item_type": item_type,
                    "collection": collection_name,
                }
                if gridfs_id_generated:
                    log_extras_upsert["gridfs_id_ref"] = str(gridfs_id_generated)
                spider.logger.debug(
                    "MongoPipeline: Upserted item into MongoDB", extra=log_extras_upsert
                )
            except OperationFailure as e:
                error_extra = {
                    "event_type": "mongodb_upsert_operation_failure",
                    "pipeline_class": self.__class__.__name__,
                    "url": url,
                    "item_type": item_type,
                    "collection": collection_name,
                    "error": str(e),
                }
                if "document too large" in str(e).lower():
                    error_extra["reason"] = "document_too_large"
                    error_extra["approx_item_dict_str_len"] = len(str(item_dict))
                spider.logger.error(
                    "MongoPipeline: MongoDB operation failure during upsert", extra=error_extra
                )
                raise DropItem(f"MongoDB operation failed for {url}: {e}")
            except Exception as e:  # Catch any other unexpected errors during upsert
                spider.logger.error(
                    "MongoPipeline: Unexpected error upserting item",
                    extra={
                        "event_type": "mongodb_upsert_unexpected_error",
                        "pipeline_class": self.__class__.__name__,
                        "url": url,
                        "item_type": item_type,
                        "collection": collection_name,
                        "error": str(e),
                        "traceback": (
                            logging.Formatter().formatException(logging.sys.exc_info())
                            if logging.sys
                            else str(e)
                        ),
                    },
                )
                raise DropItem(f"Unexpected error for {url}: {e}")
        return item
