import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
AGENT_DIR = Path(__file__).parent
BASE_DIR = AGENT_DIR.parent
sys.path.append(str(BASE_DIR / "search-agent"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService
from collector_v3 import Chunker
from data_cleaner import DataCleaner
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("embed-ocr")

def embed_ocr_diagnostics():
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    vdb = VectorDBClient(host=qdrant_host, port=qdrant_port)
    embedder = EmbeddingService()
    chunker = Chunker()
    cleaner = DataCleaner()
    
    diag_dir = BASE_DIR / "ocr_diagnostics"
    if not diag_dir.exists():
        log.error(f"Directory {diag_dir} not found.")
        return

    md_files = [f for f in os.listdir(diag_dir) if f.lower().endswith(".md")]
    log.info(f"🚀 Found {len(md_files)} MD files in {diag_dir}")
    
    all_chunks = []
    for filename in md_files:
        filepath = diag_dir / filename
        log.info(f"--- Processing: {filename} ---")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Remove OCR headers if any
            text = re.sub(r'^# OCR Result:.*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'^## PAGE \d+.*$', '', text, flags=re.MULTILINE)
            
            # Basic cleanup
            text = cleaner.clean_text(text)
            
            # Chunks
            # source name is filename without ext
            source_name = filename.replace(".md", "")
            chunks = chunker.chunk(text, source_name, str(filepath))
            
            # Add metadata about source
            for c in chunks:
                c['metadata']['source_file'] = filename
                c['metadata']['source_type'] = "ocr_diagnostic"
                c['metadata']['extracted_at'] = datetime.now().isoformat()

            all_chunks.extend(chunks)
            log.info(f"  Extracted {len(chunks)} chunks from {filename}")
        except Exception as e:
            log.error(f"  Failed to process {filename}: {e}")

    if not all_chunks:
        log.warning("No chunks to inject.")
        return

    log.info(f"Injecting {len(all_chunks)} chunks into Vector DB...")
    # Using the strategy from collector_v3
    texts_to_embed = [f"{c['title']} {c['content']}" for c in all_chunks]
    try:
        vectors = embedder.embed_texts(texts_to_embed)
        vdb.upsert_chunks(all_chunks, vectors)
        log.info("🎉 Injection complete.")
    except Exception as e:
        log.error(f"Injection failed: {e}")

import re # Needed for regex in the script

if __name__ == "__main__":
    embed_ocr_diagnostics()
