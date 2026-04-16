import fitz  # PyMuPDF
import os
import re

class PDFProcessor:
    def __init__(self):
        pass

    def classify_document(self, text, filename):
        """
        Classify document level based on keywords from classification_rules.json.
        """
        # Exhaustive safety checks
        t = text if text is not None else ""
        f = filename if filename is not None else "Unknown"
        
        title_text = (f + " " + t[:500]).lower()
        
        # Training/Admin keywords
        if any(kw in title_text for kw in ["tlu", "thủy lợi", "đhtl", "quy chế nội bộ"]):
            return 5
        if any(kw in title_text for kw in ["giáo dục đại học", "đại học", "văn bằng"]):
            return 4
        if any(kw in title_text for kw in ["giáo dục", "dạy và học"]):
            return 3
        if any(kw in title_text for kw in ["viên chức", "đơn vị sự nghiệp"]):
            return 2
        if any(kw in title_text for kw in ["luật", "nghị định", "thông tư"]):
            return 1
        return 5

    def extract_text_by_article(self, pdf_path):
        """
        Extract text from PDF and split into chunks based on Articles (Điều).
        """
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        level = self.classify_document(full_text, os.path.basename(pdf_path))
        articles = re.split(r'(?i)\n\s*(Điều\s+\d+[:\.])', full_text)
        
        chunks = []
        if len(articles) > 1:
            for i in range(1, len(articles), 2):
                article_title = articles[i].strip()
                article_content = articles[i+1].strip() if i+1 < len(articles) else ""
                chunks.append({
                    "title": f"{os.path.basename(pdf_path)} - {article_title}",
                    "content": article_content,
                    "metadata": {
                        "source": os.path.basename(pdf_path),
                        "type": "regulation",
                        "level": level
                    }
                })
        else:
            words = full_text.split()
            chunk_size = 500
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                chunks.append({
                    "title": f"{os.path.basename(pdf_path)} - Chunk {i//chunk_size + 1}",
                    "content": chunk,
                    "metadata": {
                        "source": os.path.basename(pdf_path),
                        "type": "general",
                        "level": level
                    }
                })
        return chunks

if __name__ == "__main__":
    print("PDFProcessor and Classification initialized.")
