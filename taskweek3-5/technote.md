# TLU Smart Tutor - Technical Documentation

## 🏗️ System Architecture

Hệ thống được xây dựng theo kiến trúc Microservices hướng sự kiện (Event-Driven), tập trung vào khả năng trích xuất và truy vấn tri thức pháp quy chính xác.

### 1. Frontend (Next.js)
- **Port:** 3000
- **Công nghệ:** Next.js, TailwindCSS, Lucide-react.
- **Chức năng:** Giao diện người dùng cho tra cứu RAG và bảng điều khiển quản trị (Admin Dashboard) để quản lý luồng OCR/Embedding.

### 2. Search API (FastAPI)
- **Port:** 8003
- **Công nghệ:** FastAPI, Uvicorn, Rank-BM25.
- **Tính năng nổi bật:** 
    - **Hybrid Search Engine:** Kết hợp giữa tìm kiếm ngữ nghĩa (Dense Vector) và tìm kiếm từ khóa (BM25) để đảm bảo độ chính xác khi tra cứu các thuật ngữ pháp lý hoặc số Điều/Khoản cụ thể.
    - **Admin API:** Cung cấp các endpoint điều phối quy trình OCR và nạp dữ liệu (Ingestion).

### 3. Collector Agent
- **Scripts chính:** `collector_v3.py`, `smart_pipeline_v2.py`.
- **Chức năng:** Tự động hóa việc thu thập dữ liệu từ Hanhchinh.tlu.edu.vn và Thuvienphapluat.vn.
- **Thư viện:** Playwright (sync), BeautifulSoup4.

### 4. OCR Pipeline (Chandra & High-Fidelity Extraction)
- **Core Orchestrator:** `pdf_processor.py`.
- **Cơ chế hoạt động:** 
    - **Cloud High-Fidelity (Kaggle Bridge):** Sử dụng `chandra_bot.py` để gửi tác vụ lên Kaggle GPU T4. 
    - **Runner Tối ưu:** `kaggle_chandra_runner.py` sử dụng logic official từ Chandra 2, tự động snapping ảnh về bội số của 28 và giới hạn pixel (~1.2M) để tránh lỗi bộ nhớ VRAM.
    - **Safe-Naming:** Tự động khử dấu tiếng Việt và chuẩn hóa tên file để tránh lỗi encoding trong môi trường Linux/Kaggle.
    - **Fallback Local (EasyOCR):** Tự động kích hoạt khi Cloud OCR gặp sự cố, đảm bảo dữ liệu luôn được trích xuất.

### 5. Vector Database & Message Queue
- **Qdrant (Port 6335):** Lưu trữ vector tri thức.
- **RabbitMQ (Port 5672):** Điều phối tác vụ giữa các Agent và Worker ngầm.
- **Worker (`mq_worker.py`):** Xử lý nạp dữ liệu và OCR ở chế độ nền.

## 📚 Thư viện cốt lõi
- `sentence-transformers`: Tạo embedding đa ngôn ngữ (paraphrase-multilingual-MiniLM-L12-v2).
- `qdrant-client`: Quản trị và truy vấn cơ sở dữ liệu Vector.
- `rank-bm25`: Thuật toán chấm điểm từ khóa cho Hybrid Search.
- `pymupdf (fitz)`: Xử lý cấu trúc file PDF.

## 🛠️ Case/Chiến lược xử lý dữ liệu

### 1. Phân mảnh theo Điều/Khoản (Article-level Chunking)
Hệ thống không chia nhỏ văn bản theo độ dài cố định (fixed size) mà sử dụng Regex thông minh:
- **Case xử lý:** Nhận diện các điểm ngắt `Điều X`, `Chương Y`, kể cả khi có định dạng Markdown (`**Điều X**`).
- **Lợi ích:** Đảm bảo khi User hỏi về một Điều cụ thể, AI sẽ trả về trọn vẹn ngữ cảnh của Điều đó, tránh bị cắt nửa chừng.

### 2. Làm sạch dữ liệu OCR
- **Case xử lý:** Loại bỏ header/footer thừa, sửa lỗi khoảng trắng do OCR, chuẩn hóa các ký tự Unicode tiếng Việt trước khi đưa vào mô hình Embedding.

### 3. Cơ chế Hybrid Search (Weighted Search)
- **Case xử lý:** Khi User nhập "Điều 3", Vector search có thể tìm thấy nhiều Điều tương tự, nhưng BM25 sẽ "kéo" Điều 3 chính xác lên Top 1 nhờ trùng khớp từ khóa tuyệt đối.

### 4. Dự phòng OCR (Hybrid Pipeline)
- **Case xử lý:** Hệ thống ưu tiên Chandra OCR để lấy Layout (Table, Math, Headers). Nếu Kaggle API phản hồi chậm (>10 phút) hoặc lỗi, EasyOCR local sẽ tiếp quản.
- **Tối ưu VRAM:** Runner trên Kaggle được cấu hình đặc biệt để xử lý các file lớn (>15 trang) bằng cách dọn dẹp bộ nhớ đệm GPU sau mỗi trang.
