import requests
import os
import sys

def download_confirmed_pdf():
    # This is a verified direct link to a TLU Training Regulation PDF (Non-viewer version)
    url = "https://tlus.edu.vn/wp-content/uploads/2021/09/Quy-dinh-dao-tao-dai-hoc-theo-tin-chi-2021.pdf"
    save_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_downloads"
    save_path = os.path.join(save_dir, "QuyCheDaoTao_Final.pdf")
    
    print(f"Connecting to: {url}")
    try:
        # Use verify=False to bypass SSL issues on university servers
        response = requests.get(url, verify=False, timeout=30)
        if response.status_code == 200:
            content_size = len(response.content)
            if content_size > 5000: # Ensure it's not a 404 page
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"SUCCESS: Downloaded {content_size} bytes to {save_path}")
            else:
                print(f"FAILED: File too small ({content_size} bytes). Likely 404.")
        else:
            print(f"FAILED: Status Code {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    download_confirmed_pdf()
