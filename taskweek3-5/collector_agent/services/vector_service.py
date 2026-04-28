from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

class VectorService:
    def __init__(self, host="localhost", port=6335):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "tlu_regulations"

    def ensure_collection(self, vector_size: int = 384):
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            print(f"[DB] Creating collection {self.collection_name}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
        else:
            print(f"[DB] Collection {self.collection_name} already exists.")

    def upsert_points(self, points):
        return self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
    def delete_collection(self):
        print(f"[DB] Deleting collection {self.collection_name}...")
        self.client.delete_collection(self.collection_name)
