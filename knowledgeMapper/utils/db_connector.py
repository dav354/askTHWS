import config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

_mongo_client = None


async def get_db_connection():
    """
    Establishes and returns an async connection to MongoDB.
    Uses a singleton pattern for the client to ensure connection pooling.
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            host=config.MONGO_HOST,
            port=config.MONGO_PORT,
            username=config.MONGO_USER,
            password=config.MONGO_PASS,
            authSource="admin",
            authMechanism="SCRAM-SHA-1",
            directConnection=True,
        )
    db = _mongo_client[config.MONGO_DB_NAME]
    fs = AsyncIOMotorGridFSBucket(db)
    return _mongo_client, db, fs
