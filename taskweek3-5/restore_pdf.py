import base64
import os
import json

def restore_pdf():
    # Read the output from Step 1265
    output_path = r"C:\Users\pc\.gemini\antigravity\brain\7e7a6854-7a60-49c4-a6c5-c16aec1f1a42\.system_generated\steps\1265\output.txt"
    target_path = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw\QuyCheDaoTao2021_REAL.pdf"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data.get('status') == 'PDF_CAPTURED':
        b64 = data['base64']
        with open(target_path, 'wb') as f:
            f.write(base64.b64decode(b64))
        print(f"--- RESTORE SUCCESS ---")
        print(f"File: {target_path}")
        print(f"Size: {os.path.getsize(target_path)} bytes")
    else:
        print("FAILED: No captured PDF in output.")

if __name__ == "__main__":
    restore_pdf()
