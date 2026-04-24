import os

# ĐÂY LÀ PHIÊN BẢN SCRIPT (.PY) TỰ CÀI ĐẶT THƯ VIỆN
# VÌ ID CHANDRA-OCR-ENGINE BỊ KHÓA Ở CHẾ ĐỘ SCRIPT
code_content = r"""
import subprocess
import sys
import os

def install_deps():
    print("🛠️ Đang cài đặt thư viện (PyMuPDF, vLLM)... Vui lòng đợi...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymupdf", "vllm>=0.5.0", "beautifulsoup4", "pandas", "tqdm"])
    print("✅ Cài đặt hoàn tất!")

# Cài đặt trước khi import fitz
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
        print(f"Step 2: Initializing LLM {model_id} (Lite Mode)...")
        self.llm = LLM(model=model_id, trust_remote_code=True, max_model_len=8192, gpu_memory_utilization=0.8)
        self.params = SamplingParams(temperature=0.0, max_tokens=4096, stop=["<|im_end|>", "<|endoftext|>"])

    def process_large_file(self, pdf_path):
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        final_md = f"# OCR KẾT QUẢ: {os.path.basename(pdf_path)}\n\n"
        
        for i in range(total_pages):
            print(f"\n[PROCESS] Quét trang {i+1}/{total_pages}...")
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            width, height = img.size
            mid = height // 2
            overlap = 200
            tiles = [img.crop((0, 0, width, mid + overlap)), img.crop((0, mid - overlap, width, height))]
            
            page_html = ""
            for j, t in enumerate(tiles):
                print(f"  - Xử lý phân vùng {j+1}/2...")
                out = self.llm.generate({"prompt": f"<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>OCR this image to HTML with data-bbox and data-label.<|im_end|>\n<|im_start|>assistant\n", "multi_modal_data": {"image": t}}, sampling_params=self.params)
                page_html += out[0].outputs[0].text
            
            soup = BeautifulSoup(page_html, 'html.parser')
            blocks = soup.find_all("div", attrs={"data-label": ["Section-Header", "Text", "Table"]})
            final_md += f"\n\n## TRANG {i+1}\n"
            for b in blocks:
                label, content = b.get("data-label"), b.get_text().strip()
                if label == "Section-Header": final_md += f"\n### {content}\n"
                elif label == "Table": final_md += f"\n{str(b.table)}\n"
                else: final_md += f"{content} "
            print(f"✅ Đã xong trang {i+1}.")
            
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
    print(f"🎯 Khởi động OCR: {os.path.basename(target_file)}")
    try:
        master = ChandraMaster()
        md_output = master.process_large_file(target_file)
        with open("final_high_fidelity_ocr.md", "w", encoding="utf-8") as f:
            f.write(md_output)
        print("\n✨ TẤT CẢ ĐÃ XONG! Kết quả tại 'final_high_fidelity_ocr.md'.")
    except Exception as e:
        print(f"\n❌ LỖI CHÍ MẠNG: {str(e)}")
else:
    print("❌ LỖI: Không tìm thấy file PDF nào!")
"""

with open(r'C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\kaggle_chandra_engine\kaggle_chandra_runner.py', 'w', encoding='utf-8') as f:
    f.write(code_content)

print("Self-installing script generated successfully.")
