import os
import sys
from pathlib import Path

# Fix terminal encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append('collector_agent')
from pdf_processor import PDFProcessor

def test_dual():
    proc = PDFProcessor()
    raw_dir = Path("data_raw_v2")
    out_dir = Path("data_ocr_text")
    out_dir.mkdir(exist_ok=True)
    
    # Chon 1 file tieu bieu
    target_name = None
    for f in os.listdir(raw_dir):
        if "đào tạo trực tuyến" in f.lower():
            target_name = f
            break
            
    if not target_name:
        print("❌ Khong tim thay file PDF!")
        return

    filepath = raw_dir / target_name
    print(f"🚀 Dang quet OCR (Dual Output) cho: {target_name}")
    
    # 1. Chay OCR (Lay thong tin thuc te)
    chunks = proc.extract_text_by_article(str(filepath))
    
    # 2. Xuat file TEXT (.txt)
    txt_path = out_dir / f"{target_name}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"--- SOURCE: {target_name} ---\n\n")
        for c in chunks:
            f.write(f"[PAGE {c['metadata'].get('page')} | {c['title']}]\n{c['content']}\n\n")
            f.write("-" * 40 + "\n")

    # 3. Xuat file MARKDOWN (.md)
    md_path = out_dir / f"{target_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 📄 OCR Audit: {target_name}\n\n")
        f.write(f"## 📚 Noi dung chi tiet\n")
        for c in chunks:
            f.write(f"### 📍 Trang {c['metadata'].get('page')} - {c['title']}\n")
            f.write(f"```text\n{c['content']}\n```\n\n---\n")

    print(f"✅ HOAN THANH!")
    print(f"1. File Text: {txt_path}")
    print(f"2. File Markdown: {md_path}")

if __name__ == "__main__":
    test_dual()
