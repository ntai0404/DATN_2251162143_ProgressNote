import torch, os, fitz
from PIL import Image
from bs4 import BeautifulSoup
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

class KaggleChandraRunner:
    """
    Standard Chandra OCR Runner using Transformers library (Official Method).
    Optimized for Kaggle T4 GPU.
    """
    def __init__(self, model_id="datalab-to/chandra-ocr-2"):
        print(f"🚀 Loading Official Chandra Model: {model_id}")
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id, 
            torch_dtype="auto", 
            device_map="auto", 
            trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        print("✅ Model loaded successfully.")

    def process_pdf(self, pdf_path, output_path):
        doc = fitz.open(pdf_path)
        final_md = ""
        
        for i in range(len(doc)):
            print(f"📄 Processing Page {i+1}/{len(doc)}...")
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Standard Qwen2-VL prompt format
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": "OCR this image to HTML with data-bbox and data-label."}
                ]
            }]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt"
            ).to("cuda")

            generated_ids = self.model.generate(**inputs, max_new_tokens=4096)
            generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
            output_text = self.processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            
            # Simple extraction from HTML-like output
            soup = BeautifulSoup(output_text, 'html.parser')
            final_md += f"\n\n## PAGE {i+1}\n" + soup.get_text().strip()
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        print(f"✨ Finished! Saved to {output_path}")

if __name__ == "__main__":
    # Test script for local or kaggle
    test_pdf = "test_sample.pdf"
    if os.path.exists(test_pdf):
        runner = KaggleChandraRunner()
        runner.process_pdf(test_pdf, "output.md")
