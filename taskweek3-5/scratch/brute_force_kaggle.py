import os
import sys
import re
import time
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load credentials
load_dotenv(Path(__file__).parent / ".env")

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_EXE = r"C:\Users\pc\AppData\Local\Programs\Python\Python311\Scripts\kaggle.exe"
BASE_DIR = Path(__file__).parent.parent
ENGINE_DIR = BASE_DIR / "kaggle_chandra_engine"
UPLOAD_DIR = BASE_DIR / "kaggle_upload_temp"

OCR_RESULTS_DIR = BASE_DIR / "data_extracted" / "chandra_ocr"
OCR_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_command_with_retry(cmd, name, max_retries=15):
    """Chạy lệnh với cơ chế thử lại cực kỳ kiên trì"""
    for i in range(max_retries):
        print(f"--- Attempting {name} (Attempt {i+1}/{max_retries}) ---")
        try:
            # Sử dụng subprocess với timeout lớn để tránh treo
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
            
            if result.returncode == 0:
                print(f"DONE {name} Succeeded!")
                return True
            
            # Kiểm tra xem có thông báo thành công dù return code lỗi không
            output = result.stdout + result.stderr
            if "successfully pushed" in output or "Upload successful" in output:
                print(f"WARN {name} likely succeeded despite error code.")
                return True
                
            print(f"FAIL {name} failed.")
            print(f"Error: {result.stderr.strip()[:200]}")
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {name} timed out, but might be processing on server...")
            # Với Kaggle, timeout thường là do server chưa trả về kịp nhưng lệnh đã tới
            if name == "Upload" or name == "Push Kernel":
                return True
        except Exception as e:
            print(f"🔥 Unexpected error: {e}")
            
        print(f"Retrying {name} in 15 seconds...")
        time.sleep(15)
    return False

def brute_force_flow():
    # 1. Sync Data (Upload)
    # Chúng ta dùng 'datasets create' nếu chưa có, hoặc 'version' nếu có rồi
    # Đảm bảo metadata chuẩn
    slug = "chandra-ocr-input-v3" # Dùng slug mới hoàn toàn để tránh 403/404
    meta = {"title": "Chandra OCR Input V3", "id": f"{KAGGLE_USERNAME}/{slug}", "licenses": [{"name": "CC0-1.0"}]}
    import json
    with open(UPLOAD_DIR / "dataset-metadata.json", "w") as f: json.dump(meta, f)
    
    print("PHASE 1: UPLOADING DATA...")
    if not run_command_with_retry([KAGGLE_EXE, "datasets", "create", "-p", str(UPLOAD_DIR), "--public"], "Upload"):
        # Nếu create lỗi (do đã tồn tại), thử version
        run_command_with_retry([KAGGLE_EXE, "datasets", "version", "-p", str(UPLOAD_DIR), "-m", "Retry sync"], "Upload Version")

    # 2. Trigger Kernel
    print("PHASE 2: TRIGGERING OCR ENGINE...")
    # Cập nhật metadata kernel
    kernel_meta_path = ENGINE_DIR / "kernel-metadata.json"
    with open(kernel_meta_path, "r") as f: k_meta = json.load(f)
    k_meta["id"] = f"{KAGGLE_USERNAME}/chandra-ocr-engine-v3"
    k_meta["dataset_sources"] = [f"{KAGGLE_USERNAME}/{slug}"]
    with open(kernel_meta_path, "w") as f: json.dump(k_meta, f)
    
    if not run_command_with_retry([KAGGLE_EXE, "kernels", "push", "-p", str(ENGINE_DIR)], "Push Kernel"):
        print("Could not trigger kernel. Aborting.")
        return

    # 3. Wait and Download
    print("PHASE 3: POLLING FOR RESULTS...")
    kernel_id = f"{KAGGLE_USERNAME}/chandra-ocr-engine-v3"
    max_wait_mins = 30
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait_mins * 60:
        res = subprocess.run([KAGGLE_EXE, "kernels", "status", kernel_id], capture_output=True, text=True)
        status = res.stdout.lower()
        print(f"Status check: {status.strip()}")
        
        if "complete" in status:
            print("OCR COMPLETE! Downloading...")
            if run_command_with_retry([KAGGLE_EXE, "kernels", "output", kernel_id, "-p", str(OCR_RESULTS_DIR)], "Download"):
                print("ALL DONE! RESULTS ARE IN data_extracted/chandra_ocr")
                return
        elif "error" in status:
            print("Kernel failed. Stopping.")
            return
            
        time.sleep(60) # Chờ 1 phút check 1 lần

if __name__ == "__main__":
    brute_force_flow()
