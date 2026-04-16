from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

class VectorDBClient:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "tlu_regulations"

    def init_collection(self, vector_size=384): # Updated for paraphrase-multilingual-MiniLM-L12-v2
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
            print(f"Collection {self.collection_name} deleted for realignment.")
            
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        print(f"Collection {self.collection_name} created with size {vector_size}.")

    def upsert_chunks(self, chunks, vectors):
        points = []
        import hashlib
        for chunk, vector in zip(chunks, vectors):
            # Create a unique ID from title and content hash
            content_hash = hashlib.md5(f"{chunk['title']}{chunk['content']}".encode()).hexdigest()
            # Qdrant prefers UUID string or integer. We'll use a deterministic approach.
            points.append(models.PointStruct(
                id=content_hash[:32], # Use hex string as ID
                vector=vector,
                payload={
                    "title": chunk["title"],
                    "content": chunk["content"],
                    **chunk["metadata"]
                }
            ))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Upserted {len(points)} points.")

    def search(self, query_vector, limit=5):
        # Modern migration to query_points for 1.17+ compatibility
        try:
            return self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit
            ).points
        except AttributeError:
            # Fallback for older versions if necessary
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )

if __name__ == "__main__":
    vdb = VectorDBClient()
    # vdb.init_collection()
    print("VectorDBClient initialized.")
