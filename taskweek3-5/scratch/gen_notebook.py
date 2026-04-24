import json, os

code_lines = [
    "# ==========================================\n",
    "# 1. KHỞI TẠO MÔI TRƯỜNG CHUẨN\n",
    "# ==========================================\n",
    "!pip install -q pymupdf vllm>=0.5.0 beautifulsoup4 pandas tqdm\n",
    "\n",
    "import os, torch, fitz\n",
    "from PIL import Image\n",
    "from bs4 import BeautifulSoup\n",
    "from vllm import LLM, SamplingParams\n",
    "from tqdm import tqdm\n",
    "\n",
    "# --- 2. LOGIC OCR CHUYÊN NGHIỆP (COMPACT) ---\n",
    "class ChandraMaster:\n",
    "    def __init__(self, model_id=\"datalab-to/chandra-ocr-2\"):\n",
    "        self.llm = LLM(model=model_id, trust_remote_code=True, max_model_len=12288, gpu_memory_utilization=0.9)\n",
    "        self.params = SamplingParams(temperature=0.0, max_tokens=8192, stop=[\"<|im_end|>\", \"<|endoftext|>\"])\n",
    "\n",
    "    def process_large_file(self, pdf_path):\n",
    "        doc = fitz.open(pdf_path)\n",
    "        final_md = f\"# OCR KẾT QUẢ: {os.path.basename(pdf_path)}\\n\\n\"\n",
    "        for i in range(len(doc)):\n",
    "            page = doc[i]\n",
    "            pix = page.get_pixmap(dpi=300)\n",
    "            img = Image.frombytes(\"RGB\", [pix.width, pix.height], pix.samples)\n",
    "            # Tiling logic to avoid OOM\n",
    "            width, height = img.size\n",
    "            mid = height // 2\n",
    "            overlap = 200\n",
    "            tiles = [img.crop((0, 0, width, mid + overlap)), img.crop((0, mid - overlap, width, height))]\n",
    "            \n",
    "            page_html = \"\"\n",
    "            for t in tiles:\n",
    "                out = self.llm.generate({\"prompt\": f\"<|im_start|>user\\n<|vision_start|><|image_pad|><|vision_end|>OCR this image to HTML with data-bbox and data-label.<|im_end|>\\n<|im_start|>assistant\\n\", \"multi_modal_data\": {\"image\": t}}, sampling_params=self.params)\n",
    "                page_html += out[0].outputs[0].text\n",
    "            \n",
    "            # Contextual Mapping\n",
    "            soup = BeautifulSoup(page_html, 'html.parser')\n",
    "            blocks = soup.find_all(\"div\", attrs={\"data-label\": [\"Section-Header\", \"Text\", \"Table\"]})\n",
    "            final_md += f\"\\n\\n## TRANG {i+1}\\n\"\n",
    "            for b in blocks:\n",
    "                label, content = b.get(\"data-label\"), b.get_text().strip()\n",
    "                if label == \"Section-Header\": final_md += f\"\\n### {content}\\n\"\n",
    "                elif label == \"Table\": final_md += f\"\\n{str(b.table)}\\n\"\n",
    "                else: final_md += f\"{content} \"\n",
    "        return final_md\n",
    "\n",
    "# --- 3. TỰ ĐỘNG TÌM FILE LỚN NHẤT & CHẠY ---\n",
    "INPUT_DIR = \"/kaggle/input/\"\n",
    "largest_file = None\n",
    "max_size = 0\n",
    "\n",
    "print(\"🔍 Đang tìm file PDF lớn nhất...\")\n",
    "for root, _, files in os.walk(INPUT_DIR):\n",
    "    for f in files:\n",
    "        if f.endswith(\".pdf\"):\n",
    "            fp = os.path.join(root, f)\n",
    "            size = os.path.getsize(fp)\n",
    "            if size > max_size:\n",
    "                max_size, largest_file = size, fp\n",
    "\n",
    "if largest_file:\n",
    "    print(f\"🎯 Đã tìm thấy file 'khủng': {os.path.basename(largest_file)} ({max_size/1024/1024:.2f} MB)\")\n",
    "    master = ChandraMaster()\n",
    "    md_output = master.process_large_file(largest_file)\n",
    "    \n",
    "    with open(\"final_high_fidelity_ocr.md\", \"w\", encoding=\"utf-8\") as f:\n",
    "        f.write(md_output)\n",
    "    print(\"✨ XONG! Kết quả đã lưu tại 'final_high_fidelity_ocr.md'.\")\n",
    "else:\n",
    "    print(\"❌ Không tìm thấy file PDF nào trong /kaggle/input!\")\n"
]

notebook = {
    "cells": [
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {"trusted": True},
            "outputs": [],
            "source": code_lines
        }
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.12"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(r'C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\kaggle_chandra_engine\kaggle_chandra_runner.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print("Notebook generated successfully.")
