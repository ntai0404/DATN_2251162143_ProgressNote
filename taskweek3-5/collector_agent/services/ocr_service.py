import os
import time
import subprocess
from pathlib import Path
from typing import Optional

class ChandraOCRService:
    def __init__(self, kaggle_executable: str = None):
        self.kaggle_exe = kaggle_executable or r"C:\Users\pc\AppData\Local\Programs\Python\Python311\Scripts\kaggle.exe"
        
    def trigger_ocr(self, pdf_path: str, dataset_id: str = "nguynxunti/chandra-ocr-input-task") -> bool:
        """
        Triggers OCR by pushing the PDF to Kaggle dataset and running the kernel.
        """
        print(f"[OCR] Triggering OCR for {pdf_path}...")
        # 1. Update dataset with the new PDF
        if not self._update_dataset(pdf_path, dataset_id):
            return False
            
        # 2. Trigger Kaggle Kernel
        if not self._run_kernel("nguynxunti/chandra-ocr-engine"):
            return False
            
        return True

    def _update_dataset(self, file_path: str, dataset_id: str) -> bool:
        print(f"[OCR] Updating dataset {dataset_id} with {file_path}...")
        try:
            # Create a temp folder for upload to avoid uploading whole directory
            temp_upload = Path("kaggle_upload_temp")
            temp_upload.mkdir(exist_ok=True)
            
            # Clear old files in temp
            for f in temp_upload.glob("*"):
                os.remove(f)
                
            # Copy target file as input.pdf
            import shutil
            shutil.copy2(file_path, temp_upload / "input.pdf")
            
            # Run kaggle datasets version
            cmd = [self.kaggle_exe, "datasets", "version", "-p", str(temp_upload), "-m", f"OCR Task {int(time.time())}", "--dir-mode", "zip"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[OCR ERROR] Dataset update failed: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"[OCR ERROR] Exception in _update_dataset: {e}")
            return False

    def _run_kernel(self, kernel_id: str) -> bool:
        print(f"[OCR] Pushing kernel {kernel_id}...")
        try:
            # We need the kernel metadata file to exist in the engine dir
            engine_dir = Path("kaggle_chandra_engine")
            cmd = [self.kaggle_exe, "kernels", "push", "-p", str(engine_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[OCR ERROR] Kernel push failed: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"[OCR ERROR] Exception in _run_kernel: {e}")
            return False

    def check_status(self, kernel_id: str = "nguynxunti/chandra-ocr-engine") -> str:
        """Returns: running, complete, error"""
        try:
            cmd = [self.kaggle_exe, "kernels", "status", kernel_id]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if "running" in result.stdout: return "running"
            if "complete" in result.stdout: return "complete"
            if "error" in result.stdout: return "error"
            return "unknown"
        except:
            return "error"
