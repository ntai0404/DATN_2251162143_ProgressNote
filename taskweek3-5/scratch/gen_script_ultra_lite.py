import os

# ULTRA-LITE VERSION FOR T4 GPU (0.5 UTILIZATION TO AVOID OOM)
code_content = r"""
import subprocess
import sys
import os

def install_deps():
    print("Step 1: Installing dependencies (PyMuPDF, vLLM)... Please wait...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymupdf", "vllm>=0.5.0", "beautifulsoup4", "pandas", "tqdm"])
    print("Success: Dependencies installed!")

try:
    import fitz
except ImportError:
    install_deps()
    import fitz

import torch
from PIL import Image
from bs4 import BeautifulSoup
from vllm import LLM, SamplingParams
from tqdm import tqdm

class ChandraMaster:
    def __init__(self, model_id="datalab-to/chandra-ocr-2"):
        print(f"Step 2: Initializing LLM {model_id} (Ultra-Lite Mode)...")
        # Reduced utilization to 0.5 and max_model_len to 4096 for T4 stability
        self.llm = LLM(model=model_id, trust_remote_code=True, max_model_len=4096, gpu_memory_utilization=0.5)
        self.params = SamplingParams(temperature=0.0, max_tokens=2048, stop=["<|im_end|>", "<|endoftext|>"])

    def process_large_file(self, pdf_path):
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        final_md = f"# OCR RESULTS: {os.path.basename(pdf_path)}\n\n"
        
        for i in range(total_pages):
            print(f"\n[PROCESS] Scanning page {i+1}/{total_pages}...")
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            width, height = img.size
            mid = height // 2
            overlap = 200
            tiles = [img.crop((0, 0, width, mid + overlap)), img.crop((0, mid - overlap, width, height))]
            
            page_html = ""
            for j, t in enumerate(tiles):
                print(f"  - Processing region {j+1}/2...")
                out = self.llm.generate({"prompt": f"<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>OCR this image to HTML with data-bbox and data-label.<|im_end|>\n<|im_start|>assistant\n", "multi_modal_data": {"image": t}}, sampling_params=self.params)
                page_html += out[0].outputs[0].text
            
            soup = BeautifulSoup(page_html, 'html.parser')
            blocks = soup.find_all("div", attrs={"data-label": ["Section-Header", "Text", "Table"]})
            final_md += f"\n\n## PAGE {i+1}\n"
            for b in blocks:
                label, content = b.get("data-label"), b.get_text().strip()
                if label == "Section-Header": final_md += f"\n### {content}\n"
                elif label == "Table": final_md += f"\n{str(b.table)}\n"
                else: final_md += f"{content} "
            print(f"Done page {i+1}.")
            
        return final_md

# --- AUTO-RUN ---
INPUT_DIR = "/kaggle/input/"
target_file = None
for root, _, files in os.walk(INPUT_DIR):
    for f in files:
        if f.endswith(".pdf"):
            fp = os.path.join(root, f)
            if os.path.getsize(fp) > 0:
                target_file = fp
                break
    if target_file: break

if target_file:
    print(f"Starting OCR: {os.path.basename(target_file)}")
    try:
        master = ChandraMaster()
        md_output = master.process_large_file(target_file)
        with open("final_high_fidelity_ocr.md", "w", encoding="utf-8") as f:
            f.write(md_output)
        print("\nALL DONE! Results saved at 'final_high_fidelity_ocr.md'.")
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
else:
    print("ERROR: No PDF file found!")
"""

with open(r'C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\kaggle_chandra_engine\kaggle_chandra_runner.py', 'w', encoding='utf-8') as f:
    f.write(code_content)

print("Ultra-Lite script generated successfully.")
