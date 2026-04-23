import os
import torch
import fitz
from PIL import Image
from transformers import BitsAndBytesConfig

# Import from official chandra library (installed via pip)
from chandra.model.schema import BatchInputItem
from chandra.model.hf import generate_hf
from chandra.settings import settings
from chandra.output import parse_markdown

class KaggleChandraRunner:
    """
    Kaggle-optimized Chandra OCR Runner.
    Uses 4-bit quantization and reduced DPI to prevent CUDA Out Of Memory on T4.
    """
    def __init__(self, model_id="datalab-to/chandra-ocr-2"):
        # Apply Kaggle T4 limits
        settings.MAX_OUTPUT_TOKENS = 4096
        settings.IMAGE_DPI = 150  # Reduced from 192 to save VRAM
        settings.MODEL_CHECKPOINT = model_id
        
        print(f"🚀 Loading Model {model_id} in 4-bit quantization (Kaggle T4 Safe)...")
        self.model = self._load_quantized_model()

    def _load_quantized_model(self):
        from transformers import AutoModelForImageTextToText, AutoProcessor
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        
        model = AutoModelForImageTextToText.from_pretrained(
            settings.MODEL_CHECKPOINT,
            device_map="auto",
            quantization_config=quantization_config,
            attn_implementation="sdpa",
            trust_remote_code=True
        )
        model = model.eval()
        
        processor = AutoProcessor.from_pretrained(settings.MODEL_CHECKPOINT, trust_remote_code=True)
        processor.tokenizer.padding_side = "left"
        model.processor = processor
        return model

    def process_pdf(self, pdf_path, output_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        doc = fitz.open(pdf_path)
        final_md = ""
        
        for i in range(len(doc)):
            print(f"📄 Processing Page {i+1}/{len(doc)}...")
            page = doc[i]
            pix = page.get_pixmap(dpi=settings.IMAGE_DPI)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Prepare item for Chandra
            item = BatchInputItem(image=img, prompt_type="ocr_layout")
            
            # Generate HTML using official Chandra logic
            results = generate_hf([item], self.model, max_output_tokens=settings.MAX_OUTPUT_TOKENS)
            raw_html = results[0].raw
            
            # Convert HTML to beautiful markdown using official parser
            md_text = parse_markdown(
                raw_html, 
                include_images=False, 
                include_headers_footers=False
            )
            
            final_md += f"\n\n## PAGE {i+1}\n" + md_text
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        print(f"✨ Finished! Saved to {output_path}")

if __name__ == "__main__":
    test_pdf = "(2025) Quy định sử dụng hệ thống quản lý học tập (LMS) tại Trường Đại học Thủy lợi..pdf"
    if os.path.exists(test_pdf):
        runner = KaggleChandraRunner()
        runner.process_pdf(test_pdf, "output.md")
