import fitz # PyMuPDF
import os

def scan_pdfs():
    raw_dir = "data_raw"
    search_term = "bổng"
    found_files = []
    
    for filename in os.listdir(raw_dir):
        if filename.endswith(".pdf"):
            path = os.path.join(raw_dir, filename)
            try:
                doc = fitz.open(path)
                # Just check first 2 pages
                text = ""
                for i in range(min(2, len(doc))):
                    text += doc[i].get_text()
                
                if search_term.lower() in text.lower():
                    print(f"FOUND in {filename}: {text[:100]}...")
                    found_files.append(filename)
                doc.close()
            except:
                continue
                
    if not found_files:
        print("NO PDF containing 'bổng' found in data_raw/")

if __name__ == "__main__":
    scan_pdfs()
