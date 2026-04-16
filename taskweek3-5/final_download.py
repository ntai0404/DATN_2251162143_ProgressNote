import requests
import os

def final_step():
    # Verified direct source for the 2021 Training Regulation
    url = "https://thuyloihcm.edu.vn/wp-content/uploads/2021/09/Quy-dinh-dao-tao-dai-hoc-theo-tin-chi-2021.pdf"
    save_path = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_downloads\QuyCheDaoTao2021_Verified.pdf"
    
    print(f"Attempting final download from: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, verify=False, timeout=60)
        if r.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(r.content)
            size = os.path.getsize(save_path)
            print(f"--- DOWNLOAD SUCCESS ---")
            print(f"File: {save_path}")
            print(f"Size: {size} bytes")
        else:
            print(f"FAILED: Status {r.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    final_step()
