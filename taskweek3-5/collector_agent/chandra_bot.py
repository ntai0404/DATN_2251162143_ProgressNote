import os
import sys
import time
import json
import subprocess
import shutil
import re
from pathlib import Path

# Force stdout encoding to utf-8 to avoid charmap errors
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

# ĐỊNH NGHĨA CÁC THÔNG SỐ CHUẨN
KAGGLE_EXE = r"C:\Users\pc\AppData\Local\Programs\Python\Python311\Scripts\kaggle.exe"
BASE_DIR = Path(__file__).parent.parent
ENGINE_DIR = BASE_DIR / "kaggle_chandra_engine"
UPLOAD_DIR = BASE_DIR / "kaggle_upload_temp"
RESULTS_DIR = BASE_DIR / "ocr_diagnostics"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# THÔNG SỐ ACC KAGGLE
KAGGLE_USER = "nguynxunti"
DATASET_ID = f"{KAGGLE_USER}/chandra-ocr-input"
KERNEL_ID = f"{KAGGLE_USER}/chandra-ocr-engine"

def log(msg):
    try:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
    except:
        print(f"[{time.strftime('%H:%M:%S')}] {msg.encode('utf-8', 'replace').decode('cp1252', 'replace')}", flush=True)

def force_run(cmd, name):
    """Ép lệnh chạy bằng được, thử lại không giới hạn cho đến khi thành công"""
    retry_count = 0
    while True:
        retry_count += 1
        log(f"Running {name} (Attempt {retry_count})...")
        try:
            # Tăng timeout lên 600s cho mỗi lần gọi
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = process.communicate(timeout=600)
            
            output = stdout + stderr
            if process.returncode == 0 or "successfully" in output.lower() or "upload successful" in output.lower():
                log(f"SUCCESS: {name}")
                return True
            
            log(f"FAILED: {name}. Error: {stderr.strip()[:100]}")
        except subprocess.TimeoutExpired:
            log(f"TIMEOUT: {name}. Kaggle server is slow, but action might have landed.")
            # Với Upload/Push, timeout thường nghĩa là đã tới server
            if name in ["Sync Data", "Trigger GPU"]: return True
        except Exception as e:
            log(f"EXCEPTION: {e}")
            
        log("Waiting 30s before retry...")
        time.sleep(30)

def main_pipeline(target_file=None):
    log("--- STARTING ULTIMATE CHANDRA BOT ---")
    
    # Xóa folder upload cũ để làm sạch
    if UPLOAD_DIR.exists(): shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir()
    
    pdfs = []
    if target_file:
        target_path = Path(target_file)
        if target_path.exists():
            pdfs.append(target_path)
            log(f"Single file mode: {target_path.name}")
        else:
            log(f"Error: Target file not found: {target_file}")
            return False
    else:
        log("Batch mode: Scanning data_raw_v2...")
        pdfs = list((BASE_DIR / "data_raw_v2").glob("*.pdf"))
        
    if not pdfs:
        log("No PDFs found to process.")
        return False
        
    # Copy và đổi tên các file - DÙNG TÊN CỰC NGẮN ĐỂ TRÁNH LỖI ENCODING
    log(f"Preparing {len(pdfs)} files for sync...")
    for pdf_file in pdfs:
        safe_name = "input.pdf"
        shutil.copy(pdf_file, UPLOAD_DIR / safe_name)
    log(f"Prepared safe files.")

    # BƯỚC 1: CẬP NHẬT DỮ LIỆU (Sync)
    meta = {"title": "Chandra OCR Input", "id": DATASET_ID, "licenses": [{"name": "CC0-1.0"}]}
    with open(UPLOAD_DIR / "dataset-metadata.json", "w") as f: json.dump(meta, f)
    
    log("Syncing Dataset...")
    force_run([KAGGLE_EXE, "datasets", "version", "-p", str(UPLOAD_DIR), "-m", f"AutoSync {time.time()}"], "Sync Data")

    # BƯỚC 2: KÍCH HOẠT GPU
    log("Pushing Kernel...")
    k_meta_path = ENGINE_DIR / "kernel-metadata.json"
    with open(k_meta_path, "r") as f: k_meta = json.load(f)
    k_meta["id"] = KERNEL_ID
    k_meta["dataset_sources"] = [DATASET_ID]
    with open(k_meta_path, "w") as f: json.dump(k_meta, f)
    
    # Ép Kaggle dùng T4 GPU
    push_cmd = [KAGGLE_EXE, "kernels", "push", "-p", str(ENGINE_DIR), "--accelerator", "NvidiaTeslaT4"]
    force_run(push_cmd, "Trigger GPU")

    # BƯỚC 3: THEO DÕI VÀ TẢI KẾT QUẢ
    log("Monitoring Status...")
    while True:
        status_proc = subprocess.run([KAGGLE_EXE, "kernels", "status", KERNEL_ID], capture_output=True, text=True, encoding='utf-8')
        status = status_proc.stdout.lower()
        log(f"Status: {status.strip()}")
        
        if "complete" in status:
            log("Job Complete! Downloading results via API...")
            try:
                from kaggle.api.kaggle_api_extended import KaggleApi
                api = KaggleApi()
                api.authenticate()
                api.kernels_output(KERNEL_ID, path=str(RESULTS_DIR))
                log("DONE! Mission accomplished. Files saved to: " + str(RESULTS_DIR))
                return True
            except Exception as e:
                log(f"API Download error (ignored if files exist): {e}")
                # Kiểm tra xem file md có tải về được không (tìm file vừa tạo gần đây nhất)
                if list(RESULTS_DIR.glob("**/*.md")):
                    log("Markdown files found! Success anyway.")
                    return True
                else:
                    log("Waiting 30s before retry...")
            # log("ERROR: Kernel failed. Re-triggering...")
            # force_run(push_cmd, "Trigger GPU")
            pass
            
        time.sleep(60)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    main_pipeline(target)
