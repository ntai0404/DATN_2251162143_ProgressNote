import fitz  # PyMuPDF
import os
from pathlib import Path

class PDFHandler:
    def __init__(self):
        pass

    def check_pdf_type(self, pdf_path: str) -> str:
        """
        Phân loại PDF: 'digital' (có text layer) hoặc 'scanned' (cần OCR).
        """
        try:
            doc = fitz.open(pdf_path)
            total_text_len = 0
            # Kiểm tra 3 trang đầu (hoặc tất cả nếu ít hơn 3)
            sample_pages = min(3, len(doc))
            for i in range(sample_pages):
                total_text_len += len(doc[i].get_text().strip())
            
            doc.close()
            
            # Ngưỡng: Nếu trung bình mỗi trang có ít hơn 50 ký tự -> Coi là PDF Scan
            if total_text_len / sample_pages < 50:
                return "scanned"
            return "digital"
        except Exception as e:
            print(f"[PDF] Lỗi khi kiểm tra file: {e}")
            return "unknown"

    def extract_digital_text(self, pdf_path: str) -> str:
        """
        Trích xuất trực tiếp cho Digital PDF (Nhanh & Sạch).
        """
        print(f"[PDF] Extracting direct text from {pdf_path}...")
        doc = fitz.open(pdf_path)
        full_md = "# EXTRACTED TEXT: " + Path(pdf_path).name + "\n\n"
        
        for i, page in enumerate(doc):
            full_md += f"## PAGE {i+1}\n\n"
            full_md += page.get_text() + "\n\n"
            
        doc.close()
        return full_md
