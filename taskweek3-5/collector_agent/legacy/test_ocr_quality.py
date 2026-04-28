
import sys
import os
import logging

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Fix for Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from pdf_processor import PDFProcessor

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def test_ocr():
    processor = PDFProcessor()
    
    # Path to small PDF
    pdf_path = r"c:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw\2019 Di?u ch?nh quy trnh ch?m thi t? lu?n.pdf"
    
    # Handle potentially mangled PowerShell path names
    if not os.path.exists(pdf_path):
        # List files and try to match
        raw_dir = r"c:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw"
        files = os.listdir(raw_dir)
        for f in files:
            if "2019" in f and "chậm thi" in f.lower() or "chấm thi" in f.lower():
                pdf_path = os.path.join(raw_dir, f)
                break

    print(f"Testing OCR on: {pdf_path}")
    if not os.path.exists(pdf_path):
        print("Error: PDF file not found!")
        return

    chunks = processor.extract_text_by_article(pdf_path)
    
    print("\n" + "="*50)
    print("OCR RESULT PREVIEW (First 2 chunks):")
    print("="*50)
    for i, chunk in enumerate(chunks[:2]):
        print(f"\n[Chunk {i+1}] Title: {chunk['title']}")
        print(f"Content: {chunk['content'][:500]}...")
    print("="*50)

if __name__ == "__main__":
    test_ocr()
