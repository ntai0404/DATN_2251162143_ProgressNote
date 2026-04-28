import os
import sys
import time
import json
import subprocess
import shutil
import re
from pathlib import Path
from unidecode import unidecode

# Force stdout encoding to utf-8 to avoid charmap errors
os.environ["PYTHONIOENCODING"] = "utf-8"
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

# ĐỊNH NGHĨA CÁC THÔNG SỐ CHUẨN
import shutil
KAGGLE_EXE = shutil.which("kaggle") or "kaggle"
BASE_DIR = Path(__file__).parent.parent

# Import TextRefiner
sys.path.append(str(BASE_DIR))
try:
    from shared.text_refiner import TextRefiner
    refiner = TextRefiner()
except Exception as e:
    print(f"Warning: Could not import TextRefiner: {e}")
    refiner = None

ENGINE_DIR = BASE_DIR / "kaggle_chandra_engine"
UPLOAD_DIR = BASE_DIR / "kaggle_upload_temp"
RESULTS_DIR = BASE_DIR / "ocr_diagnostics"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# THÔNG SỐ ACC KAGGLE
KAGGLE_USER = "nguynxunti"
KERNEL_ID = f"{KAGGLE_USER}/chandra-ocr-engine"

def sanitize_vietnamese_name(name):
    """Chuẩn hóa tên file: bỏ dấu, thay khoảng trắng bằng gạch dưới, bỏ ký tự đặc biệt"""
    # Bỏ dấu tiếng Việt bằng unidecode
    name = unidecode(name)
    # Thay thế ký tự không phải chữ/số bằng gạch dưới
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Loại bỏ gạch dưới trùng lặp
    name = re.sub(r'_+', '_', name).strip('_')
    return name.lower()

def log(msg):
    try:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
    except:
        print(f"[{time.strftime('%H:%M:%S')}] {msg.encode('utf-8', 'replace').decode('cp1252', 'replace')}", flush=True)

def wait_for_dataset_ready(dataset_id, timeout=300):
    """Đợi cho đến khi dataset ở trạng thái 'ready' trên Kaggle"""
    log(f"Waiting for dataset {dataset_id} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        proc = subprocess.run([KAGGLE_EXE, "datasets", "status", dataset_id], capture_output=True, text=True, encoding='utf-8')
        status = proc.stdout.strip().lower()
        if "ready" in status:
            log("Dataset is READY.")
            return True
        log(f"Current status: {status or 'unknown'}. Waiting 10s...")
        time.sleep(10)
    log("Timeout waiting for dataset readiness.")
    return False

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

def main_pipeline(target_file=None, output_name=None):
    log("--- STARTING ULTIMATE CHANDRA BOT (v2.1 Stable) ---")
    
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
        log("Batch mode: Scanning data_raw...")
        pdfs = list((BASE_DIR / "data_raw" / "hanhchinh").glob("*.pdf"))
        
    if not pdfs:
        log("No PDFs found to process.")
        return False
        
    # Copy file - DÙNG TÊN CỐ ĐỊNH ĐỂ RUNNER DỄ TÌM
    log(f"Preparing {len(pdfs)} files for sync...")
    for pdf_file in pdfs:
        # Trong mode single, ta chỉ cần 1 file input.pdf
        shutil.copy(pdf_file, UPLOAD_DIR / "input.pdf")
    log(f"Prepared safe files.")

    # BƯỚC 1: ĐỒNG BỘ DATA QUA DATASET CỐ ĐỊNH (VERSIONED)
    stable_slug = "chandra-ocr-input-task"
    unique_id = f"{KAGGLE_USER}/{stable_slug}"
    
    # Kiểm tra dataset đã tồn tại chưa
    status_proc = subprocess.run([KAGGLE_EXE, "datasets", "status", unique_id], capture_output=True, text=True)
    exists = status_proc.returncode == 0
    
    # Tạo metadata
    dataset_metadata = {
        "title": "Chandra OCR Input Task",
        "id": unique_id,
        "licenses": [{"name": "CC0-1.0"}]
    }
    with open(UPLOAD_DIR / "dataset-metadata.json", "w") as f:
        json.dump(dataset_metadata, f)
        
    if not exists:
        log(f"Creating NEW stable dataset: {unique_id}...")
        force_run([KAGGLE_EXE, "datasets", "create", "-p", str(UPLOAD_DIR)], "Create Dataset")
    else:
        log(f"Updating EXISTING stable dataset: {unique_id}...")
        # Sử dụng version instead of create
        force_run([KAGGLE_EXE, "datasets", "version", "-p", str(UPLOAD_DIR), "-m", f"Task {int(time.time())}"], "Update Dataset Version")
    
    # Đợi dataset READY
    if not wait_for_dataset_ready(unique_id):
        log("WARNING: Dataset not ready, but attempting to proceed anyway...")
    
    # Cập nhật kernel-metadata.json
    kernel_meta_path = ENGINE_DIR / "kernel-metadata.json"
    with open(kernel_meta_path, "r") as f:
        kernel_meta = json.load(f)
    
    kernel_meta["dataset_sources"] = [unique_id]
    with open(kernel_meta_path, "w") as f:
        json.dump(kernel_meta, f, indent=4)

    # BƯỚC 2: KÍCH HOẠT GPU
    log("Pushing Kernel...")
    # ÉP sử dụng T4 vì P100 không hỗ trợ tốt một số kernel của vLLM/Transformers mới
    push_cmd = [KAGGLE_EXE, "kernels", "push", "-p", str(ENGINE_DIR), "--accelerator", "NvidiaTeslaT4"]
    force_run(push_cmd, "Trigger GPU")

    # BƯỚC 3: THEO DÕI VÀ TẢI KẾT QUẢ
    log("Monitoring Status...")
    while True:
        status_proc = subprocess.run([KAGGLE_EXE, "kernels", "status", KERNEL_ID], capture_output=True, text=True, encoding='utf-8')
        status = status_proc.stdout.lower()
        log(f"Status: {status.strip()}")
        
        if "complete" in status:
            log("Job Complete! Downloading results via Kaggle CLI...")
            try:
                TEMP_DOWNLOAD = RESULTS_DIR / "temp_download"
                if TEMP_DOWNLOAD.exists(): shutil.rmtree(TEMP_DOWNLOAD)
                TEMP_DOWNLOAD.mkdir(parents=True, exist_ok=True)
                
                dl_cmd = [KAGGLE_EXE, "kernels", "output", KERNEL_ID, "-p", str(TEMP_DOWNLOAD)]
                dl_proc = subprocess.run(dl_cmd, capture_output=True, text=True, encoding='utf-8')
                
                # Refine text if possible
                downloaded_file = TEMP_DOWNLOAD / "final_high_fidelity_ocr.md"
                if downloaded_file.exists() and refiner:
                    log("Applying TextRefiner to fix hallucinations...")
                    with open(downloaded_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    refined = refiner.refine(content)
                    with open(downloaded_file, "w", encoding="utf-8") as f:
                        f.write(refined)

                # 1. Save to ocr_diagnostics first (User principle)
                for f in TEMP_DOWNLOAD.glob("*"):
                    dest = RESULTS_DIR / f.name
                    if dest.exists(): dest.unlink()
                    shutil.copy(str(f), str(dest))
                
                log("DONE! Mission accomplished. Files synced to ocr_diagnostics.")
                
                # 1. Save to ocr_diagnostics first (User principle)
                diag_dir = BASE_DIR / "ocr_diagnostics"
                diag_dir.mkdir(parents=True, exist_ok=True)
                
                downloaded_file = TEMP_DOWNLOAD / "final_high_fidelity_ocr.md"
                if downloaded_file.exists():
                    if output_name:
                        diag_dest = diag_dir / f"{output_name}.md"
                        shutil.copy(str(downloaded_file), str(diag_dest))
                        log(f"SAVED TO DIAGNOSTICS: {diag_dest}")
                        
                        target_dir = BASE_DIR / "data_extracted" / "chandra_ocr" / "ocr_results"
                        target_dir.mkdir(parents=True, exist_ok=True)
                        final_dest = target_dir / f"{output_name}.md"
                        shutil.move(str(downloaded_file), str(final_dest))
                        log(f"MOVED TO INGESTION QUEUE: {final_dest}")
                    else:
                        log("WARNING: No output_name provided.")
                
                if TEMP_DOWNLOAD.exists(): shutil.rmtree(TEMP_DOWNLOAD)
                return True
            except Exception as e:
                log(f"Download error: {e}")
                time.sleep(30)
            
        time.sleep(60)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    out_name = sys.argv[2] if len(sys.argv) > 2 else None
    main_pipeline(target, out_name)
