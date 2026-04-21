import fitz
import os

def scan():
    raw_dir = 'data_raw'
    if not os.path.exists(raw_dir):
        print("Folder data_raw not found.")
        return
        
    pdf_files = [f for f in os.listdir(raw_dir) if f.lower().endswith('.pdf')]
    print(f"Scanning {len(pdf_files)} PDFs...")
    
    playable = []
    for f in pdf_files:
        try:
            doc = fitz.open(os.path.join(raw_dir, f))
            text = "".join([p.get_text() for p in doc])
            if len(text.strip()) > 200:
                playable.append((f, len(text)))
        except:
            continue
            
    print(f"\nFound {len(playable)} PDFs with extractable text:")
    for name, length in playable:
        print(f"- {name} ({length} chars)")
        
    print(f"\nTotal extractable: {len(playable)} / {len(pdf_files)}")

if __name__ == "__main__":
    scan()
