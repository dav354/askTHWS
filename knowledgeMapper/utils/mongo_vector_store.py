from .db_connector import get_db_connection
from typing import List, Dict, Any

class MongoVectorStore:
    def __init__(self, db_name: str, collection_name: str, vector_index_name: str):
        self.db_name = db_name
        self.collection_name = collection_name
        self.vector_index_name = vector_index_name
        self.client = None
        self.db = None
        self.collection = None

    async def ainit(self):
        self.client, self.db, _ = await get_db_connection()
        self.collection = self.db[self.collection_name]

    async def create_vector_index(self, vector_field: str = "vector", num_dimensions: int = 768, metric: str = "cosine"):
        index_spec = {
            "name": self.vector_index_name,
            "key": {vector_field: "vector"},
            "definition": {
                "fields": [{
                    "type": "vector",
                    "path": vector_field,
                    "numDimensions": num_dimensions,
                    "similarity": metric
                }]
            }
        }
    
        try:
            await self.collection.create_search_index(index_spec)
            print(f"[*] Vector search index '{self.vector_index_name}' created successfully.")
        except Exception as e:
            print(f"[!] Error creating vector search index '{self.vector_index_name}': {e}")
    

    async def add_vectors(self, documents: List[Dict[str, Any]]):
        if documents:
            await self.collection.insert_many(documents)

    async def similarity_search(self, query_vector: List[float], k: int = 4) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": query_vector,
                    "path": "vector",
                    "numCandidates": k * 10,  # Search more candidates for better recall
                    "limit": k,
                    "index": self.vector_index_name
                }
            },
            {
                "$project": {
                    "_id": 0,  # Exclude _id from results
                    "page_content": "$page_content",
                    "metadata": "$metadata",
                    "score": { "$meta": "vectorSearchScore" }
                }
            }
        ]
        results = []
        async for doc in self.collection.aggregate(pipeline):
            results.append(doc)
        return results

    async def close(self):
        if self.client:
            self.client.close()