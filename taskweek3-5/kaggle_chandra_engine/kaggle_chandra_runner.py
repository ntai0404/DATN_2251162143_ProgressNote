import os
import torch
import fitz  # PyMuPDF
from PIL import Image
from bs4 import BeautifulSoup
from vllm import LLM, SamplingParams

class KaggleChandraRunner:
    def __init__(self, model_id="datalab-to/chandra-ocr-2", use_tiling=True):
        print(f"🚀 Initializing Chandra v2 on vLLM Engine...")
        self.use_tiling = use_tiling
        
        # vLLM setup optimized for T4 GPU
        self.llm = LLM(
            model=model_id,
            trust_remote_code=True,
            max_model_len=16384,
            gpu_memory_utilization=0.9,
            tensor_parallel_size=1
        )
        
        self.sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            stop=["<|im_end|>", "<|endoftext|>"]
        )

        self.layout_prompt = "OCR this image to HTML with data-bbox and data-label (Section-Header, Table, Text)."

    def process_pdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        final_markdown = ""
        
        for i in range(len(doc)):
            print(f"📄 Processing Page {i+1}...")
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            if self.use_tiling:
                # --- REAL TILING LOGIC (Vertical Split with Overlap) ---
                width, height = img.size
                mid = height // 2
                overlap = 200 # pixel overlap to avoid cutting sentences
                
                tiles = [
                    img.crop((0, 0, width, mid + overlap)),        # Top half
                    img.crop((0, mid - overlap, width, height))    # Bottom half
                ]
                
                page_html = ""
                for tile in tiles:
                    page_html += self._run_inference(tile)
            else:
                page_html = self._run_inference(img)
            
            # --- CONTEXTUAL MAPPING ---
            final_markdown += f"\n\n## TRANG {i+1}\n"
            final_markdown += self._parse_to_structured_markdown(page_html)
            
        return final_markdown

    def _run_inference(self, img_obj):
        output = self.llm.generate(
            {
                "prompt": f"<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>{self.layout_prompt}<|im_end|>\n<|im_start|>assistant\n",
                "multi_modal_data": {"image": img_obj},
            },
            sampling_params=self.sampling_params
        )
        return output[0].outputs[0].text

    def _parse_to_structured_markdown(self, html):
        """Map Text blocks into their corresponding Section-Headers"""
        soup = BeautifulSoup(html, 'html.parser')
        markdown_output = []
        
        # Get all relevant blocks in document order
        blocks = soup.find_all("div", attrs={"data-label": ["Section-Header", "Text", "Table"]})
        
        for block in blocks:
            label = block.get("data-label")
            content = block.get_text().strip()
            
            if label == "Section-Header":
                # New Article/Clause
                markdown_output.append(f"\n### {content}\n")
            elif label == "Table":
                # Preserve Table structure
                markdown_output.append(f"\n{str(block.table)}\n")
            else:
                # Text content, append to current stream
                markdown_output.append(f"{content} ")
                
        return "".join(markdown_output)

if __name__ == "__main__":
    # Test path on Kaggle
    test_pdf = "/kaggle/input/tlu-data/sample.pdf"
    if os.path.exists(test_pdf):
        runner = KaggleChandraRunner(use_tiling=True)
        md_result = runner.process_pdf(test_pdf)
        with open("ocr_output.md", "w", encoding="utf-8") as f:
            f.write(md_result)
        print("✅ OCR Complete. Output saved to ocr_output.md")
