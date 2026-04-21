import fitz  # PyMuPDF
import os
import re
import logging
import numpy as np
from PIL import Image
import io

# Import OCR modules lazily
_reader = None

from pathlib import Path
from data_cleaner import DataCleaner
logger = logging.getLogger('pdf-processor')

class PDFProcessor:
    def __init__(self):
        self.article_pattern = r'(?i)(Điều\s+\d+[:\.])'
        self.cleaner = DataCleaner()
        self.diag_dir = Path(__file__).parent.parent / "ocr_diagnostics"
        self.diag_dir.mkdir(parents=True, exist_ok=True)

    def _save_diagnostics(self, filename, text):
        """Lưu kết quả OCR ra file vật lý để kiểm định mắt (md, txt)"""
        base_name = Path(filename).stem
        txt_path = self.diag_dir / f"{base_name}.txt"
        md_path = self.diag_dir / f"{base_name}.md"
        
        # 1. Lưu bản Text thuần
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        # 2. Lưu bản Markdown (để xem đẹp hơn)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# OCR Result: {filename}\n\n")
            f.write(f"**Extracted at:** {logging.Formatter('%(asctime)s').format(logging.LogRecord('', 0, '', 0, '', '', None))}\n\n")
            f.write("---\n\n")
            f.write(text)
            
        logger.info(f"Saved diagnostic files to: {self.diag_dir}")


    def get_ocr_reader(self):
        global _reader
        if _reader is None:
            import easyocr
            logger.info("Initializing EasyOCR with Vietnamese support...")
            _reader = easyocr.Reader(['vi', 'en'], gpu=False) # Chạy CPU cho ổn định trên máy local
        return _reader

    def classify_document(self, text, filename):
        t = text if text else ""
        f = filename if filename else "Unknown"
        title_text = (f + " " + t[:500]).lower()
        if any(kw in title_text for kw in ["tlu", "thủy lợi", "đhtl", "quy chế nội bộ"]): return 5
        return 3

    def _preprocess_image(self, img_np):
        """Tối ưu hóa ảnh để OCR đọc chính xác hơn (Spelling Focus)"""
        import cv2
        # 1. Chuyển sang ảnh xám
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # 2. Tăng độ tương phản & Làm sắc nét
        # Sử dụng Adaptive Thresholding để tách chữ ra khỏi nền giấy scan mờ/vàng
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 3. Khử nhiễu muối tiêu (Denoising)
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        # 4. Trả về ảnh đã xử lý
        return denoised

    def _extract_text_via_ocr(self, doc):
        """Converts PDF pages to images, preprocesses them, and runs OCR."""
        reader = self.get_ocr_reader()
        full_text = ""
        page_map = []
        offset = 0
        
        logger.info(f"Starting ADVANCED OCR for {doc.name} ({doc.page_count} pages)...")
        for page_num, page in enumerate(doc, start=1):
            # 1. Chụp ảnh trang PDF chất lượng cao (300 DPI)
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img_np = np.array(img)
            
            # 2. TIỀN XỬ LÝ ẢNH (New Upgrade)
            processed_img = self._preprocess_image(img_np)
            
            # 3. Chạy OCR trên ảnh đã làm sạch
            logger.info(f"Scanning cleaned page {page_num}...")
            result = reader.readtext(processed_img, detail=0, paragraph=True)
            page_text = "\n".join(result)
            
            # 4. Cập nhật map
            page_map.append((offset, offset + len(page_text), page_num))
            full_text += page_text + "\n"
            offset += len(page_text) + 1
            
        return full_text, page_map


    def extract_text_by_article(self, pdf_path):
        doc = fitz.open(pdf_path)
        filename = os.path.basename(pdf_path)
        
        # Thử bóc tách text thông thường trước
        full_text = ""
        page_map = []
        offset = 0
        for page_num, page in enumerate(doc, start=1):
            t = page.get_text()
            page_map.append((offset, offset + len(t), page_num))
            full_text += t
            offset += len(t)

        # KIỂM TRA: Nếu text bóc được quá ít (ví dụ < 100 ký tự cho cả file) -> PDF DẠNG ẢNH
        if len(full_text.strip()) < 100:
            logger.info(f"Detected scanned PDF (no text): {filename}. Switching to OCR...")
            full_text, page_map = self._extract_text_via_ocr(doc)

        # CƠ CHẾ LƯU HỒ SƠ KIỂM ĐỊNH (Diagnostic Files)
        self._save_diagnostics(filename, full_text)

        level = self.classify_document(full_text, filename)
        parts = re.split(self.article_pattern, full_text)


        chunks = []
        if len(parts) > 1:
            cumulative = len(parts[0])
            for i in range(1, len(parts), 2):
                article_header = parts[i].strip()
                article_content = parts[i + 1].strip() if i + 1 < len(parts) else ""
                match = re.search(r'\d+', article_header)
                article_id = int(match.group()) if match else (i // 2)
                
                # Tìm số trang dựa trên offset
                page_num = 1
                for start, end, p in page_map:
                    if start <= cumulative < end:
                        page_num = p
                        break
                
                cumulative += len(parts[i]) + len(parts[i+1] if i+1 < len(parts) else "")
                
                # Sạch hóa nội dung (Clean)
                cleaned_content = self.cleaner.clean_text(article_content)
                
                chunks.append({
                    "title": f"{filename} - {article_header}",
                    "content": cleaned_content,
                    "metadata": {
                        "source": filename, "type": "regulation", "level": level,
                        "page": page_num, "article_id": article_id
                    }
                })
        else:
            # Fallback window splitting
            words = full_text.split()
            chunk_size = 500
            for i in range(0, len(words), chunk_size):
                chunk_text = " ".join(words[i:i + chunk_size])
                cleaned_chunk = self.cleaner.clean_text(chunk_text)
                chunks.append({
                    "title": f"{filename} - Đoạn {i//chunk_size + 1}",
                    "content": cleaned_chunk,
                    "metadata": { "source": filename, "page": 1, "level": level }
                })
        
        doc.close()
        # Lọc bỏ các chunk rác hoàn toàn (Noise filtering)
        return self.cleaner.filter_noise_chunks(chunks)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("OCR-Enabled PDFProcessor ready.")
