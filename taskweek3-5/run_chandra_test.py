from kaggle_bridge import KaggleBridge

def run_specific_ocr(target_name):
    bridge = KaggleBridge()
    print(f"🚀 Starting Targeted OCR for: {target_name}")
    
    # Bước 1: Đẩy dữ liệu
    if not bridge.sync_data(target_file_name=target_name):
        print("❌ Sync failed.")
        return

    # Bước 2: Kích hoạt GPU Engine trên Kaggle
    if not bridge.trigger_kernel():
        print("❌ Kernel trigger failed.")
        return

    # Bước 3: Chờ đợi và tải kết quả (Thư mục ocr_diagnostics)
    if bridge.wait_and_download():
        # Bước 4: Làm sạch văn bản (Xử lý lỗi ký tự OCR)
        bridge.run_cleaning()
        print(f"\n✅ SUCCESS: Result should be in 'ocr_diagnostics'")
    else:
        print("❌ OCR Process failed.")

if __name__ == "__main__":
    TARGET = "(2019) Điều chỉnh quy trình chấm thi tự luận.pdf"
    run_specific_ocr(TARGET)
