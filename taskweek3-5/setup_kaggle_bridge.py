import os
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv(Path(__file__).parent / ".env")

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")

def setup_kaggle_config():
    """Tạo file kaggle.json vào thư mục mặc định của hệ thống nếu chưa có"""
    home = Path.home()
    kaggle_dir = home / ".kaggle"
    kaggle_dir.mkdir(exist_ok=True)
    
    config_file = kaggle_dir / "kaggle.json"
    config_data = {
        "username": KAGGLE_USERNAME,
        "key": KAGGLE_KEY
    }
    
    with open(config_file, "w") as f:
        json.dump(config_data, f)
    
    # Windows doesn't use chmod 600, but let's make sure it's readable
    print(f"✅ Kaggle config created at: {config_file}")

def init_kaggle_resources():
    """Khởi tạo Dataset và Notebook trên Kaggle"""
    print("🚀 Initializing Kaggle Resources...")
    
    # 1. Tạo thư mục tạm để khởi tạo dataset
    temp_dir = Path("kaggle_init_temp")
    temp_dir.mkdir(exist_ok=True)
    
    # Tạo metadata cho Dataset
    dataset_metadata = {
        "title": "Chandra OCR Input",
        "id": f"{KAGGLE_USERNAME}/chandra-ocr-input",
        "licenses": [{"name": "CC0-1.0"}]
    }
    
    with open(temp_dir / "dataset-metadata.json", "w") as f:
        json.dump(dataset_metadata, f)
    
    # Tạo một file giả để init dataset
    with open(temp_dir / "placeholder.txt", "w") as f:
        f.write("Initial placeholder")
        
    # Lệnh tạo dataset (sẽ lỗi nếu đã tồn tại, nên dùng try/except)
    subprocess.run(["kaggle", "datasets", "create", "-p", str(temp_dir)], capture_output=True)
    print("✅ Dataset initialized (or already exists).")

    # 2. Tạo metadata cho Kernel (Notebook)
    kernel_metadata = {
        "id": f"{KAGGLE_USERNAME}/chandra-ocr-engine",
        "title": "Chandra OCR Engine",
        "code_file": "kaggle_chandra_runner.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_internet": "true",
        "dataset_sources": [f"{KAGGLE_USERNAME}/chandra-ocr-input"]
    }
    
    # Lưu metadata kernel vào thư mục engine
    engine_dir = Path("kaggle_chandra_engine")
    with open(engine_dir / "kernel-metadata.json", "w") as f:
        json.dump(kernel_metadata, f)
        
    print("✅ Kernel metadata created.")

if __name__ == "__main__":
    if not KAGGLE_USERNAME or not KAGGLE_KEY:
        print("❌ Please set KAGGLE_USERNAME and KAGGLE_KEY in your .env file first!")
    else:
        setup_kaggle_config()
        init_kaggle_resources()
