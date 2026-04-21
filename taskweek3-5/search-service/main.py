"""
Search Service — TLU Smart Tutor
=================================
FastAPI microservice cho semantic search trên Vector DB.
- POST /search             → Tìm kiếm ngữ nghĩa, trả về Top-K chunks
- GET  /health             → Health check
- GET  /docs               → Swagger UI (tự động)
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add shared modules
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR / "search-agent"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

# ── App setup ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("search-service")

app = FastAPI(
    title="TLU Smart Tutor — Search Service",
    description="Semantic search API trên kho tri thức pháp lý TLU (Vector DB powered by Qdrant).",
    version="1.0.0",
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    score_threshold: Optional[float] = 0.4

class SearchResult(BaseModel):
    title: str
    content: str
    score: float
    source_url: Optional[str] = None
    page: Optional[int] = None
    article_id: Optional[int] = None
    level: Optional[int] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_found: int

# ── Singleton clients (lazy-loaded) ──────────────────────────────────────────
_vdb: Optional[VectorDBClient] = None
_embedder: Optional[EmbeddingService] = None

def get_clients():
    global _vdb, _embedder
    if _vdb is None:
        log.info("Loading Search Service clients...")
        _vdb = VectorDBClient()
        _embedder = EmbeddingService()
        log.info("Clients ready.")
    return _vdb, _embedder

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    """Kiểm tra trạng thái hoạt động của Search Service."""
    vdb, _ = get_clients()
    return {"status": "ok", "service": "search-service", "qdrant": "connected"}

@app.post("/search", response_model=SearchResponse, tags=["Search"])
def search(req: SearchRequest):
    """
    Tìm kiếm ngữ nghĩa (Semantic Search) trên kho tri thức TLU.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    vdb, embedder = get_clients()
    log.info(f"[SEARCH] Query: '{req.query}' | Top-K: {req.top_k}")

    # Embed query
    query_vector = embedder.embed_texts([req.query])[0]

    # Search in Qdrant
    raw_results = vdb.search(query_vector, limit=req.top_k)

    # Format results
    results = []
    for hit in raw_results:
        payload = hit.payload or {}
        # Metadata in Qdrant is usually nested under a 'metadata' key in payload
        meta = payload.get("metadata", {})
        
        results.append(SearchResult(
            title=payload.get("title", "N/A"),
            content=payload.get("content", ""),
            score=round(hit.score, 4),
            source_url=meta.get("source_url") or payload.get("source_url"),
            page=meta.get("page") or payload.get("page"),
            article_id=meta.get("article_id") or payload.get("article_id"),
            level=meta.get("level") or payload.get("level"),
        ))

    log.info(f"[SEARCH] Found {len(results)} results.")
    return SearchResponse(query=req.query, results=results, total_found=len(results))

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
