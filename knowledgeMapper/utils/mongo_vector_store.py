from typing import Any, Dict, List, Optional
from pymongo.operations import SearchIndexModel
from .db_connector import get_db_connection


class MongoVectorStore:
    def __init__(self, db_name: str, collection_name: str, vector_index_name: str):
        self.db_name = db_name
        self.collection_name = collection_name
        self.vector_index_name = vector_index_name
        self.client = None
        self.db = None
        self.collection = None

    async def ainit(self):
        """Initializes the async database connection."""
        if not self.client:
            self.client, self.db, _ = await get_db_connection()
            self.collection = self.db[self.collection_name]

    async def create_vector_index(
        self, vector_field: str = "vector", num_dimensions: int = 1024, metric: str = "cosine"
    ):
        """Creates the vector search index using the SearchIndexModel helper."""
        
        definition = {
            "mappings": {
                "dynamic": False,
                "fields": {
                    vector_field: {
                        "type": "knnVector",
                        "dimensions": num_dimensions,
                        "similarity": metric
                    }
                }
            }
        }

        index_model = SearchIndexModel(
            name=self.vector_index_name,
            definition=definition
        )
        # ----------------------

        try:
            await self.collection.create_search_index(index_model)
            print(f"[*] Vector search index '{self.vector_index_name}' created successfully.")
        except Exception as e:
            print(f"[!] Info creating vector search index '{self.vector_index_name}': {e}")

    async def add_vectors(self, documents: List[Dict[str, Any]]):
        """Adds a list of documents to the collection."""
        if documents:
            await self.collection.insert_many(documents)

    async def similarity_search(
        self, query_vector: List[float], k: int = 4, filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Performs an async similarity search with an optional filter."""
        vector_search_stage = {
            "$vectorSearch": {
                "queryVector": query_vector,
                "path": "vector",
                "numCandidates": k * 10,
                "limit": k,
                "index": self.vector_index_name,
            }
        }
        
        if filter:
            vector_search_stage["$vectorSearch"]["filter"] = filter
            
        pipeline = [
            vector_search_stage,
            {
                "$project": {
                    "_id": 0,
                    "page_content": "$page_content",
                    "metadata": "$metadata",
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        
        results = []
        cursor = self.collection.aggregate(pipeline)
        async for doc in cursor:
            results.append(doc)
        return results

    async def close(self):
        """Closes the client connection."""
        if self.client:
            self.client.close()
