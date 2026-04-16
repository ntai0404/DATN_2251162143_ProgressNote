import os
import sys

# PROGRAMMATIC PATH RESOLUTION FOR DEMO COHESION
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(current_dir)
sys.path.append(root_path)
sys.path.append(current_dir) # Add self folder
sys.path.append(os.path.join(root_path, "shared"))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

app = FastAPI(title="TLU Regulations Search API")
vdb_client = VectorDBClient()
embedding_service = EmbeddingService()

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class SearchResult(BaseModel):
    title: str
    content: str
    score: float
    metadata: dict

@app.get("/")
async def root():
    return {"message": "Welcome to TLU Regulations Search API"}

@app.post("/search", response_model=List[SearchResult])
async def search_regulations(request: SearchRequest):
    # Embed query
    query_vector = embedding_service.embed_texts(request.query)[0]
    
    # Search in Qdrant
    hits = vdb_client.search(query_vector, limit=request.top_k)
    
    results = []
    for hit in hits:
        results.append({
            "title": hit.payload.get("title", "Untitled"),
            "content": hit.payload.get("content", ""),
            "score": hit.score,
            "metadata": {
                "source": hit.payload.get("source", ""),
                "page": hit.payload.get("page", 0)
            }
        })
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
