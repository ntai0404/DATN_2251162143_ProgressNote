import os
import sys
import logging
from pathlib import Path

# Fix terminal encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup paths
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR / "search-agent"))
sys.path.append(str(BASE_DIR / "collector_agent"))

from pdf_processor import PDFProcessor
from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('tlu-ingest')

def total_ingest():
    processor = PDFProcessor()
    vdb = VectorDBClient()
    embedder = EmbeddingService()
    
    raw_dir = BASE_DIR / "data_raw_v2"
    ocr_out_dir = BASE_DIR / "data_ocr_text"
    ocr_out_dir.mkdir(exist_ok=True)

    if not raw_dir.exists():
        logger.error(f"Directory {raw_dir} not found.")
        return

    pdf_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".pdf")]
    logger.info(f"🚀 TOTAL INGEST: Found {len(pdf_files)} files in {raw_dir}")
    
    for filename in pdf_files:
        filepath = raw_dir / filename
        logger.info(f"--- Processing: {filename} ---")
        
        try:
            # 1. Extract chunks
            chunks = processor.extract_text_by_article(str(filepath))
            if not chunks:
                logger.warning(f"  No text could be extracted from {filename}")
                continue
                
            # 2. Save OCR Text to Audit Folder (MARKDOWN STYLE)
            audit_path = ocr_out_dir / f"{filename}.md"
            with open(audit_path, "w", encoding="utf-8") as f:
                f.write(f"# 📄 OCR Audit: {filename}\n\n")
                f.write(f"> **Status:** ✅ Successfully Processed\n")
                f.write(f"> **Chunks:** {len(chunks)} extracted\n\n")
                f.write("## 📚 Nội dung chi tiết\n\n")
                
                for c in chunks:
                    title = c.get('title', 'Unknown')
                    page = c.get('metadata', {}).get('page', '?')
                    f.write(f"### 📍 Trang {page} - {title}\n")
                    f.write(f"```text\n{c.get('content', '')}\n```\n")
                    f.write("\n---\n")

            # 3. Embedding & Ingesting
            texts_to_embed = [f"{c['title']} {c['content']}" for c in chunks]
            vectors = embedder.embed_texts(texts_to_embed)
            vdb.upsert_chunks(chunks, vectors)
            
            logger.info(f"  ✅ SUCCESS: Indexed and Saved audit for {filename} ({len(chunks)} chunks)")
            
        except Exception as e:
            logger.error(f"  ❌ ERROR processing {filename}: {e}")

    logger.info("=" * 50)
    logger.info("🎉 TOTAL INGESTION COMPLETE.")
    logger.info(f"Check OCR results in: {ocr_out_dir}")

if __name__ == "__main__":
    total_ingest()
