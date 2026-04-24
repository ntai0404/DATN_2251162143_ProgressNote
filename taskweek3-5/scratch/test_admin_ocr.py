import os
import sys
import logging
from pathlib import Path

# Thêm đường dẫn để test
sys.path.append(str(Path(__file__).parent.parent / "collector_agent"))

from pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def simulate_admin_ocr_request():
    target_pdf = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw_v2\(2011) Nội quy khu Nội trú sinh viên ĐH Thủy lợi.pdf"
    
    if not os.path.exists(target_pdf):
        logging.error(f"Test file not found: {target_pdf}")
        return
        
    logging.info(f"Admin Requested OCR for: {target_pdf}")
    
    processor = PDFProcessor()
    
    # Kích hoạt pipeline trích xuất (Bao gồm Kaggle OCR)
    chunks = processor.extract_text_by_article(target_pdf, use_cloud=True)
    
    logging.info(f"\n--- SUCCESS ---")
    logging.info(f"Total chunks extracted: {len(chunks)}")
    if chunks:
        logging.info(f"First chunk preview:\nTitle: {chunks[0]['title']}\nContent Preview: {chunks[0]['content'][:100]}...\nMetadata: {chunks[0]['metadata']}")

if __name__ == "__main__":
    simulate_admin_ocr_request()
