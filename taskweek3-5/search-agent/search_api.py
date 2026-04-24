import os
import sys
import logging
import re
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = Path(os.path.dirname(current_dir))
sys.path.append(str(root_path))
sys.path.append(current_dir)
sys.path.append(os.path.join(root_path, "shared"))
sys.path.append(os.path.join(root_path, "collector_agent"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService
from hybrid_search_engine import HybridSearchEngine
from pdf_processor import PDFProcessor
from collector_v3 import Chunker
from data_cleaner import DataCleaner

load_dotenv(os.path.join(root_path, ".env"))

app = FastAPI(title="TLU Regulations Search API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
vdb_client = VectorDBClient(host=qdrant_host, port=qdrant_port)
embedding_service = EmbeddingService()
hybrid_engine = HybridSearchEngine(embedding_service)
pdf_processor = PDFProcessor()
chunker = Chunker()
cleaner = DataCleaner()

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class SearchResult(BaseModel):
    title: str
    content: str
    score: float
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    metadata: dict

@app.get("/")
async def root():
    return {"message": "Welcome to TLU Regulations Search API"}

@app.post("/search", response_model=List[SearchResult])
async def search_regulations(request: SearchRequest):
    try:
        if not hybrid_engine.chunks:
            chunks = vdb_client.fetch_all_chunks()
            if chunks:
                hybrid_engine.fit(chunks)
        
        if hybrid_engine.chunks:
            results = hybrid_engine.search(request.query, top_k=request.top_k)
            return [{
                "title": r['chunk']['title'], 
                "content": r['chunk']['content'],
                "score": r['score'], 
                "dense_score": r['dense_score'],
                "bm25_score": r['bm25_score'], 
                "metadata": r['chunk']['metadata']
            } for r in results]
    except Exception as e:
        logging.error(f"Hybrid search failed: {e}")

    query_vector = embedding_service.embed_texts([request.query])[0]
    hits = vdb_client.search(query_vector, limit=request.top_k)
    
    results = []
    for hit in hits:
        results.append({
            "title": hit.payload.get("title", "Untitled"),
            "content": hit.payload.get("content", ""),
            "score": hit.score,
            "metadata": {k: v for k, v in hit.payload.items() if k not in ["title", "content"]}
        })
    return results

@app.post("/refresh")
async def refresh_index():
    chunks = vdb_client.fetch_all_chunks()
    if chunks:
        hybrid_engine.fit(chunks)
    return {"status": "success", "count": len(chunks)}

# ── Admin Endpoints ──────────────────────────────────────────────────────────

@app.get("/admin/files")
async def list_admin_files():
    files = []
    
    # 1. Scan data_raw/hanhchinh for original PDFs
    data_dir = root_path / "data_raw" / "hanhchinh"
    pdf_names = set()
    if data_dir.exists():
        for f in os.listdir(data_dir):
            if f.lower().endswith(".pdf"):
                rel_path = f"data_raw/hanhchinh/{f}"
                base_name = Path(f).stem
                pdf_names.add(base_name)
                
                # Check OCR status
                md_path = root_path / "ocr_diagnostics" / f"{base_name}.md"
                # Also check chandra results
                safe_name = re.sub(r'[^\x00-\x7F]+', '', f).replace(" ", "_")
                if safe_name.endswith(".pdf"): safe_name = safe_name[:-4]
                chandra_md = root_path / "data_extracted" / "chandra_ocr" / "ocr_results" / f"{safe_name}.md"
                
                has_ocr = md_path.exists() or chandra_md.exists()
                
                files.append({
                    "name": f,
                    "path": rel_path,
                    "type": "PDF",
                    "has_ocr": has_ocr
                })

    # 2. Scan ocr_diagnostics for MD files that might not have a matching PDF in data_raw
    diag_dir = root_path / "ocr_diagnostics"
    if diag_dir.exists():
        for f in os.listdir(diag_dir):
            if f.lower().endswith(".md"):
                base_name = Path(f).stem
                if base_name not in pdf_names:
                    files.append({
                        "name": f,
                        "path": f"ocr_diagnostics/{f}",
                        "type": "MD",
                        "has_ocr": True
                    })
                    
    return files

class OCRRequest(BaseModel):
    path: str
    mode: Optional[str] = "cloud"

@app.post("/admin/ocr")
async def trigger_ocr(request: OCRRequest, background_tasks: BackgroundTasks):
    full_path = root_path / request.path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.path}")
    
    def run_ocr():
        pdf_processor.extract_text_by_article(str(full_path), use_cloud=(request.mode == "cloud"))
        
    background_tasks.add_task(run_ocr)
    return {"status": "processing", "file": full_path.name}

@app.get("/admin/ocr-content/{fileName}")
async def get_ocr_content(fileName: str):
    base_name = Path(fileName).stem
    md_path = root_path / "ocr_diagnostics" / f"{base_name}.md"
    
    # Try alternate location
    safe_name = re.sub(r'[^\x00-\x7F]+', '', fileName).replace(" ", "_")
    if safe_name.endswith(".pdf"): safe_name = safe_name[:-4]
    chandra_md = root_path / "data_extracted" / "chandra_ocr" / "ocr_results" / f"{safe_name}.md"

    target = md_path if md_path.exists() else (chandra_md if chandra_md.exists() else None)
    
    if target and target.exists():
        with open(target, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"error": "OCR content not found"}

class EmbedRequest(BaseModel):
    filename: str

@app.post("/admin/embed")
async def trigger_embed(request: EmbedRequest, background_tasks: BackgroundTasks):
    base_name = Path(request.filename).stem
    md_path = root_path / "ocr_diagnostics" / f"{base_name}.md"
    
    if not md_path.exists():
        # Try alternate
        safe_name = re.sub(r'[^\x00-\x7F]+', '', request.filename).replace(" ", "_")
        if safe_name.endswith(".pdf"): safe_name = safe_name[:-4]
        md_path = root_path / "data_extracted" / "chandra_ocr" / "ocr_results" / f"{safe_name}.md"

    if not md_path.exists():
        raise HTTPException(status_code=404, detail="OCR file not found")

    def run_embed():
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Basic cleanup
        cleaned_text = cleaner.clean_text(text)
        chunks = chunker.chunk(cleaned_text, base_name, str(md_path))
        
        if chunks:
            texts = [f"{c['title']} {c['content']}" for c in chunks]
            vectors = embedding_service.embed_texts(texts)
            vdb_client.upsert_chunks(chunks, vectors)

    background_tasks.add_task(run_embed)
    return {"status": "processing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
