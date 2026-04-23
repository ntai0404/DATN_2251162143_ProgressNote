import os
import subprocess
import shutil

class KaggleChandraRunner:
    """
    Standard Chandra OCR Runner using the official `chandra-ocr` package.
    Optimized for Kaggle using the HuggingFace (hf) method locally.
    """
    def __init__(self, model_id="datalab-to/chandra-ocr-2"):
        print(f"🚀 Using official Chandra OCR CLI engine (Model: {model_id})")

    def process_pdf(self, pdf_path, output_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        output_dir = os.path.dirname(output_path) or "."
        temp_out = os.path.join(output_dir, "chandra_temp_output")
        
        # We use the official chandra CLI which handles the Qwen architecture natively
        cmd = ["chandra", pdf_path, temp_out, "--method", "hf"]
        print(f"📄 Executing: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True)
            
            # Chandra creates temp_out/<basename>/<basename>.md
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            generated_md = os.path.join(temp_out, base_name, f"{base_name}.md")
            
            if os.path.exists(generated_md):
                shutil.copy2(generated_md, output_path)
                print(f"✨ Finished! Saved to {output_path}")
            else:
                print(f"❌ Output markdown not found at {generated_md}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during Chandra execution: {e}")
        finally:
            if os.path.exists(temp_out):
                shutil.rmtree(temp_out, ignore_errors=True)

if __name__ == "__main__":
    test_pdf = "test_sample.pdf"
    if os.path.exists(test_pdf):
        runner = KaggleChandraRunner()
        runner.process_pdf(test_pdf, "output.md")
