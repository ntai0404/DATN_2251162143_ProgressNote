import fitz  # PyMuPDF
import os
import re
import logging
import numpy as np
from PIL import Image
import io
import sys
import subprocess
from pathlib import Path

# Thêm đường dẫn để import các module local
sys.path.append(str(Path(__file__).parent.parent))

from data_cleaner import DataCleaner
from text_refiner import TextRefiner

logger = logging.getLogger('pdf-processor')

class PDFProcessor:
    def __init__(self):
        self.article_pattern = r'(?i)(Điều\s+\d+[:\.])'
        self.cleaner = DataCleaner()
        self.refiner = TextRefiner()
        self.base_dir = Path(__file__).parent.parent
        self.diag_dir = self.base_dir / "ocr_diagnostics"
        self.diag_dir.mkdir(parents=True, exist_ok=True)
        self.chandra_out_dir = self.base_dir / "data_extracted" / "chandra_ocr"

    def _save_diagnostics(self, filename, text):
        base_name = Path(filename).stem
        txt_path = self.diag_dir / f"{base_name}.txt"
        md_path = self.diag_dir / f"{base_name}.md"
        
        with open(txt_path, "w", encoding="utf-8") as f: f.write(text)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# OCR Result: {filename}\n\n---\n\n{text}")

    def extract_text_by_article(self, pdf_path, use_cloud=True):
        """
        Refactored extraction: 
        1. Try standard text extraction.
        2. If scanned, check for existing Chandra OCR result.
        3. If no Chandra result and use_cloud=True, trigger Kaggle Bridge.
        """
        doc = fitz.open(pdf_path)
        filename = os.path.basename(pdf_path)
        base_name = Path(filename).stem
        
        # 1. Try standard text
        full_text = ""
        page_map = []
        offset = 0
        for page_num, page in enumerate(doc, start=1):
            t = page.get_text()
            page_map.append((offset, offset + len(t), page_num))
            full_text += t
            offset += len(t)

        # 2. Check if Scanned PDF
        if len(full_text.strip()) < 100:
            logger.info(f"Detected scanned PDF: {filename}")
            
            # Tính toán tên file an toàn (ASCII) nhưng vẫn dễ đọc
            import unicodedata
            # Chuẩn hóa tên file trước khi gửi qua Chandra
            clean_name = "".join(c for c in unicodedata.normalize('NFD', filename) if unicodedata.category(c) != 'Mn')
            safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', clean_name)
            safe_name = re.sub(r'_+', '_', safe_name).strip('_')
            
            if safe_name.lower().endswith(".pdf"):
                safe_name = safe_name[:-4]
            
            chandra_file = self.chandra_out_dir / "ocr_results" / f"{safe_name}.md"
            
            # Check for existing Chandra result first
            if chandra_file.exists():
                logger.info(f"Found existing Chandra result for {filename}")
                with open(chandra_file, "r", encoding="utf-8") as f:
                    full_text = f.read()
            elif use_cloud:
                logger.info(f"No Chandra result found. Triggering Kaggle Bridge (Bot) for {filename}...")
                try:
                    bot_script = self.base_dir / "collector_agent" / "chandra_bot.py"
                    logger.info("Bot is starting. This might take several minutes...")
                    subprocess.run([sys.executable, str(bot_script), pdf_path, safe_name], check=True)
                    
                    if chandra_file.exists():
                        logger.info(f"Cloud OCR complete. Reading result from {chandra_file}")
                        with open(chandra_file, "r", encoding="utf-8") as f:
                            full_text = f.read()
                    else:
                        logger.error("Cloud OCR finished but result file not found!")
                except Exception as e:
                    logger.error(f"KaggleBridge error: {e}")
            
            # Fallback to local OCR if still empty (Legacy EasyOCR)
            if not full_text.strip():
                logger.info("Falling back to local EasyOCR...")
                full_text, _ = self._extract_text_via_ocr(doc)

        self._save_diagnostics(filename, full_text)
        level = self.classify_document(full_text, filename)
        
        # Article splitting logic with Hierarchical Context
        chunks = []
        section_pattern = r'(?i)(Chương\s+[IVXLCDM\d]+[:\.]|Mục\s+\d+[:\.])'
        
        parts = re.split(self.article_pattern, full_text)
        if len(parts) > 1:
            current_section = "Quy định chung"
            cumulative = len(parts[0])
            
            for i in range(1, len(parts), 2):
                article_header = parts[i].strip()
                article_content = parts[i + 1].strip() if i + 1 < len(parts) else ""
                
                # Tìm xem trước Điều này có Chương/Mục nào mới không
                preceding_text = parts[i-1] if i > 0 else parts[0]
                sections = re.findall(section_pattern, preceding_text)
                if sections:
                    current_section = sections[-1].strip()

                match = re.search(r'\d+', article_header)
                article_id = int(match.group()) if match else (i // 2)
                
                # Page mapping
                page_num = 1
                for start, end, p in page_map:
                    if start <= cumulative < end:
                        page_num = p
                        break
                
                cumulative += len(parts[i]) + len(parts[i+1] if i+1 < len(parts) else "")
                cleaned_content = self.cleaner.clean_text(article_content)
                # Áp dụng bộ lọc sửa lỗi chính tả OCR
                refined_content = self.refiner.refine(cleaned_content)
                
                # [THỰC THI ĐỀ XUẤT] - Làm đẹp data (Context Enrichment)
                # Kết hợp: Tiêu đề file + Tiêu đề văn bản + Chương + Điều
                enriched_content = f"[Văn bản: {filename}] [Bối cảnh: {current_section}] [{article_header}]: {refined_content}"
                
                chunks.append({
                    "title": f"{filename} - {article_header}",
                    "content": enriched_content,
                    "raw_content": refined_content, # Giữ raw để hiển thị cho User
                    "metadata": {
                        "source": filename, "type": "regulation", "level": level,
                        "page": page_num, "article_id": article_id,
                        "section": current_section
                    }
                })
        else:
            # Paragraph splitting
            words = full_text.split()
            chunk_size = 500
            for i in range(0, len(words), chunk_size):
                chunk_text = " ".join(words[i:i + chunk_size])
                cleaned_chunk = self.cleaner.clean_text(chunk_text)
                chunks.append({
                    "title": f"{filename} - Part {i//chunk_size + 1}",
                    "content": cleaned_chunk,
                    "metadata": { "source": filename, "page": 1, "level": level }
                })
        
        doc.close()
        return self.cleaner.filter_noise_chunks(chunks)

    def _extract_text_via_ocr(self, doc):
        """Legacy local OCR using EasyOCR"""
        try:
            import easyocr
            reader = easyocr.Reader(['vi', 'en'], gpu=False)
            full_text = ""
            for page_num, page in enumerate(doc, start=1):
                pix = page.get_pixmap(dpi=200)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                result = reader.readtext(np.array(img), detail=0, paragraph=True)
                full_text += "\n".join(result) + "\n"
            return full_text, []
        except Exception as e:
            logger.error(f"Local OCR failure: {e}")
            return "", []

    def classify_document(self, text, filename):
        t = (text[:1000] + filename).lower()
        if any(kw in t for kw in ["tlu", "thủy lợi", "đhtl"]): return 5
        return 3

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Final Hierarchical Contextual PDFProcessor ready.")
