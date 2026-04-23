# Hướng dẫn triển khai OCR Chandra (Git-Native) trên Kaggle

Tài liệu này hướng dẫn cách sử dụng sức mạnh GPU T4 x2 trên Kaggle để chạy OCR cho kho dữ liệu PDF của bạn thông qua việc đồng bộ trực tiếp từ GitHub.

## 🚀 Quy trình thực hiện (2 Cell Duy Nhất)

### Cell 1: Thiết lập môi trường & Clone Repo
Dán đoạn code này vào Cell đầu tiên để kéo toàn bộ dữ liệu và code từ GitHub về máy ảo Kaggle.

```python
import os

# 1. Clone Repo (Thay URL bằng link repo thật của bạn)
!git clone https://github.com/ntai0404/DATN_2251162143_ProgressNote.git 

# 2. Di chuyển vào thư mục dự án
%cd DATN_2251162143_ProgressNote/taskweek3-5

# 3. Cài đặt các thư viện bổ trợ
!pip install -q vllm>=0.5.0 pymupdf beautifulsoup4 pandas tqdm
```

### Cell 2: Thực hiện OCR file nặng nhất
Cell này tự động quét thư mục `data_raw_v2`, tìm file PDF có dung lượng lớn nhất và tiến hành chuyển đổi sang Markdown chất lượng cao.

```python
import os, torch, fitz
from PIL import Image
from bs4 import BeautifulSoup
from vllm import LLM, SamplingParams

# Import logic từ bộ Engine trong Repo
from kaggle_chandra_engine.kaggle_chandra_runner import KaggleChandraRunner

# 1. Khởi tạo Engine (Bật Tiling=True để tránh tràn bộ nhớ GPU)
runner = KaggleChandraRunner(use_tiling=True)

# 2. Tìm file PDF lớn nhất để Test
pdf_dir = "./data_raw_v2"
largest_file = None
max_size = 0

for f in os.listdir(pdf_dir):
    if f.endswith(".pdf"):
        fp = os.path.join(pdf_dir, f)
        size = os.path.getsize(fp)
        if size > max_size:
            max_size, largest_file = size, fp

if largest_file:
    print(f"🎯 Đang xử lý file: {os.path.basename(largest_file)} ({max_size/1024/1024:.2f} MB)")
    
    # 3. Chạy OCR
    markdown_result = runner.process_pdf(largest_file)
    
    # 4. Lưu kết quả ra file
    output_path = "/kaggle/working/final_high_fidelity_ocr.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_result)
    print(f"✨ XONG! Kết quả lưu tại: {output_path}")
else:
    print("❌ Không tìm thấy file PDF!")
```

## 🛠 Lưu ý cấu hình Kaggle
1.  **Settings > Accelerator:** Chọn `GPU T4 x2`.
2.  **Settings > Internet:** Chuyển sang `On`.
3.  **Persistence:** Kết quả lưu tại `/kaggle/working` sẽ mất sau khi tắt Session, hãy nhớ nhấn **Download All** ở mục Output sau khi chạy xong.

---
*Tài liệu này được cập nhật tự động cho nhánh `test_kaggle_4_OCR`.*
