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

### 4. OCR Pipeline (Chandra Integration)
- **Core:** `pdf_processor.py`.
- **Cơ chế:** 
    - Tự động nhận diện PDF dạng ảnh (Scanned PDF).
    - **Kaggle Bridge (`chandra_bot.py`):** Khi gặp file quét, hệ thống gửi yêu cầu qua Kaggle API để chạy mô hình Transformer OCR (Chandra) giúp phục hồi Layout và ký tự tiếng Việt với độ chính xác ~100%.
    - Kết quả trả về dưới dạng Markdown sạch để chuẩn bị cho bước Chunking.

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

### 4. Dự phòng OCR (Local Fallback)
- **Case xử lý:** Nếu kết nối Kaggle Bridge gặp sự cố, hệ thống tự động sử dụng EasyOCR (local) như một phương án dự phòng để đảm bảo tiến trình không bị gián đoạn hoàn toàn.
