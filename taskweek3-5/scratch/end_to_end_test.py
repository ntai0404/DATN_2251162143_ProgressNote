import os
import sys
import logging
import numpy as np
from pathlib import Path

# Force stdout encoding to utf-8
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

# Thêm đường dẫn để import các module
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "collector_agent"))
sys.path.append(str(Path(__file__).parent.parent / "search-agent"))

from pdf_processor import PDFProcessor
from embedding_service import EmbeddingService
from hybrid_search_engine import HybridSearchEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("HybridTest")

def run_hybrid_test():
    # 1. TRÍCH XUẤT DATA (Dùng PDFProcessor đã có Tree/Context)
    pdf_path = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw_v2\(2011) Nội quy khu Nội trú sinh viên ĐH Thủy lợi.pdf"
    processor = PDFProcessor()
    
    logger.info(">>> STEP 1: Extracting Chunks with Tree Context...")
    chunks = processor.extract_text_by_article(pdf_path, use_cloud=False)
    
    # 2. KHỞI TẠO HYBRID SEARCH (Tách biệt logic)
    logger.info(">>> STEP 2: Fitting Hybrid Search Engine (BM25 + Dense + RRF)...")
    embedder = EmbeddingService()
    hybrid_engine = HybridSearchEngine(embedder)
    hybrid_engine.fit(chunks)
    
    # 3. MÔ PHỎNG USER HỎI 5 CÂU
    queries = [
        "Sinh viên nội trú có được tự ý chuyển phòng hoặc cho người khác thuê lại phòng không?",
        "Thời gian ra vào khu nội trú được quy định như thế nào?",
        "Có được nấu ăn trong phòng nội trú không?",
        "Quy định về việc tiếp khách trong phòng nội trú là gì?",
        "Nếu vi phạm nội quy thì bị xử lý như thế nào?"
    ]
    
    logger.info("\n>>> STEP 3: Evaluating Hybrid Retrieval Quality...")
    
    for q in queries:
        logger.info(f"\n[USER]: {q}")
        results = hybrid_engine.search(q, top_k=1)
        
        if results:
            res = results[0]
            logger.info(f"[HYBRID SCORE (RRF)]: {res['score']:.6f}")
            logger.info(f"[DENSE SIMILARITY]: {res['dense_score']:.4f}")
            logger.info(f"[BM25 SCORE]: {res['bm25_score']:.4f}")
            logger.info(f"[SOURCE]: {res['chunk']['title']} (Trang {res['chunk']['metadata']['page']})")
            logger.info(f"[CONTENT]:\n{res['chunk']['content'][:400]}...")
            
            # Đánh giá chất lượng
            if res['dense_score'] > 0.45 or res['bm25_score'] > 5.0:
                logger.info("=> KẾT QUẢ: [CƠM CỰC NGON] - Hybrid Search đã tìm thấy kim trong đáy bể!")
            else:
                logger.info("=> KẾT QUẢ: [CẦN CẢI THIỆN] - Có thể do query quá ngắn hoặc data thiếu.")
        else:
            logger.warning("=> KẾT QUẢ: [CỨT] - Không tìm thấy gì.")

if __name__ == "__main__":
    run_hybrid_test()
