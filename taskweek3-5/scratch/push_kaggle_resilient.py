import os
import subprocess
import time
from pathlib import Path

KAGGLE_EXE = r"C:\Users\pc\AppData\Local\Programs\Python\Python311\Scripts\kaggle.exe"
BASE_DIR = Path(__file__).parent.parent
ENGINE_DIR = BASE_DIR / "kaggle_chandra_engine"

def run_with_retry(cmd, max_retries=3):
    for i in range(max_retries):
        print(f"Executing: {' '.join(cmd)} (Attempt {i+1})")
        try:
            # We use a long timeout for the command itself
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                print("Success!")
                print(result.stdout)
                return True
            else:
                print(f"Failed with return code {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                # Sometimes it succeeds despite error (like the timeout issue)
                if "successfully pushed" in result.stdout or "Upload successful" in result.stdout:
                    print("Detected success message in output despite return code. Continuing...")
                    return True
        except subprocess.TimeoutExpired:
            print("Command timed out, but it might have succeeded on server.")
            return True # In Kaggle's case, timeout usually means it's processing
        except Exception as e:
            print(f"Error: {e}")
        
        print("Retrying in 10 seconds...")
        time.sleep(10)
    return False

if __name__ == "__main__":
    print("--- Resilient Kaggle Push ---")
    # Step 1: Push Kernel
    if run_with_retry([KAGGLE_EXE, "kernels", "push", "-p", str(ENGINE_DIR)]):
        print("Kernel pushed. Waiting 60s for it to start...")
        time.sleep(60)
        
        # Step 2: Monitor status
        print("Monitoring status...")
        for _ in range(20):
            res = subprocess.run([KAGGLE_EXE, "kernels", "status", "nguynxunti/chandra-ocr-engine"], capture_output=True, text=True)
            status = res.stdout.strip()
            print(f"Current Status: {status}")
            if "complete" in status.lower():
                print("Task Complete!")
                # Step 3: Download output
                out_dir = BASE_DIR / "data_extracted" / "chandra_ocr"
                out_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run([KAGGLE_EXE, "kernels", "output", "nguynxunti/chandra-ocr-engine", "-p", str(out_dir)])
                print(f"Results saved to {out_dir}")
                break
            if "error" in status.lower():
                print("Kernel failed. Checking logs...")
                # Try to get output anyway to see logs
                subprocess.run([KAGGLE_EXE, "kernels", "output", "nguynxunti/chandra-ocr-engine", "-p", str(BASE_DIR / "logs")])
                break
            time.sleep(60)
