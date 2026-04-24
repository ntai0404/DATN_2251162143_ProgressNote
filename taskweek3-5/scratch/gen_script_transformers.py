import os

# TRANSFORMERS ENGINE (V6) - ULTRA STABLE ON T4 GPU
code_content = r"""
import subprocess
import sys
import os

def install_deps():
    print("Step 1: Installing dependencies (Transformers, Qwen-VL)... Please wait...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymupdf", "transformers>=4.45.0", "accelerate", "torch", "qwen-vl-utils", "beautifulsoup4"])
    print("Success: Dependencies installed!")

try:
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info
except ImportError:
    install_deps()
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info

import torch
import fitz
from PIL import Image
from bs4 import BeautifulSoup

class ChandraMaster:
    def __init__(self, model_id="datalab-to/chandra-ocr-2"):
        print(f"Step 2: Initializing LLM {model_id} via Transformers (Stable Mode)...")
        # Load in 4-bit or float16 to save memory
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id, torch_dtype="auto", device_map="auto", trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

    def process_large_file(self, pdf_path):
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        final_md = f"# OCR RESULTS: {os.path.basename(pdf_path)}\n\n"
        
        for i in range(total_pages):
            print(f"\n[PROCESS] Scanning page {i+1}/{total_pages}...")
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Use whole page for better layout, or tiles if needed
            # For simplicity and stability, we use whole page first
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img},
                        {"type": "text", "text": "OCR this image to HTML with data-bbox and data-label."},
                    ],
                }
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            ).to("cuda")
            
            generated_ids = self.model.generate(**inputs, max_new_tokens=4096)
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            page_html = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
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

print("Transformers-based stable script generated successfully.")
