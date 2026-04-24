import os
from kaggle.api.kaggle_api_extended import KaggleApi

def download_safe():
    api = KaggleApi()
    api.authenticate()
    
    kernel_id = "nguynxunti/chandra-ocr-engine"
    output_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_extracted\chandra_ocr"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print(f"Downloading output and logs from {kernel_id}...")
        api.kernels_output(kernel_id, path=output_dir)
        print("Done! Files should be in data_extracted/chandra_ocr")
        
        # Read the log file if it exists
        log_file = os.path.join(output_dir, "chandra-ocr-engine.log")
        if os.path.exists(log_file):
            print("\n--- KERNEL LOG ---")
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                print(f.read()[-3000:])
            print("------------------")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_safe()
