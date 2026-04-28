# BÁO CÁO TIẾN ĐỘ HỆ THỐNG - TUẦN 3-5 (CHỈNH SỬA CẬP NHẬT)
**Dự án:** Multi-Agent AI System for TLU Internal Regulations Consultation

## 1. Cấu trúc Hệ thống (Architecture)
Hệ thống được thiết kế theo kiến trúc Microservices (Multi-Agent) sử dụng **RabbitMQ** để điều phối tác vụ và **Qdrant** làm Vector Database.

- **Collector Agent (Ingestion layer):** 
  - Chịu trách nhiệm cào dữ liệu, xử lý PDF và đẩy vào Vector DB.
  - Thư mục: `collector_agent/`
- **Search Agent (Retrieval layer):**
  - Cung cấp REST API (FastAPI) để thực hiện tìm kiếm ngữ nghĩa.
  - Thư mục: `search-agent/` (Sử dụng dấu gạch nối `-`).
- **Data Layer:**
  - **Qdrant:** Chạy trên cổng `6333` (Vector storage).
  - **RabbitMQ:** Chạy trên cổng `5672` (Message queue).

## 2. Nguồn dữ liệu & Cơ chế thu thập
### Nguồn Link Chính:
1. **HCTLU Administrative Portal:** `hanhchinh.tlu.edu.vn` (Nguồn binary PDF).
2. **Thư viện pháp luật:** `thuvienphapluat.vn` (Nguồn luật bổ trợ).

### Thu hoạch dữ liệu:
- **Số lượng:** 121 file PDF quy chế bản gốc.
- **Cơ chế:** Brute-force TabID (quét toàn bộ dải ID ẩn) kết hợp Playwright để tự động đăng nhập và tải binary trực tiếp từ server.

## 3. Xử lý & Chuẩn bị dữ liệu cho AI
1. **Trích xuất (OCR/Text Extraction):** Chuyển PDF sang Text thô, giữ lại cấu trúc văn bản.
2. **Phân mảnh (Article-level Chunking):** Sử dụng Regex để tách text theo cấu trúc "Điều 1...", "Điều 2...". 
3. **Phân loại (Classification):** Tự động gán nhãn 5 cấp bậc pháp lý dựa trên bộ quy tắc `classification_rules.json`.
4. **Vector hóa:** Chuyển đổi text sang vector 384 dimensions sử dụng model `paraphrase-multilingual-MiniLM-L12-v2` (tối ưu cho tiếng Việt).

## 4. Cơ chế Tìm kiếm (Search Engine)
- **Search API:** Chạy tại cổng **8003** (`http://localhost:8003/search`).
- **Xử lý Retrieval:** Sử dụng cơ chế `query_points` của Qdrant 1.17+ để tìm kiếm nội dung có độ tương đồng cao nhất với câu hỏi.
- **Dữ liệu sẵn sàng:** Toàn bộ 121 file đã được index và sẵn sàng cho các Agent khác tra cứu.

## 5. Hướng dẫn sử dụng Demo App
Ứng dụng demo Python chạy tại cổng **3001**.

- **Cách chạy:** `python demo_app.py`
- **Chức năng:** Cho phép nhập câu hỏi tiếng Việt và nhận về trích dẫn chính xác kèm Metadata (Tên file gốc, Cấp bậc văn bản).
- **Lệnh hệ thống từ thư mục DATN:**
  ```powershell
  cd "C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5"
  python demo_app.py
  ```

---
*Báo cáo được chuẩn hóa để phục vụ thuyết minh đồ án tốt nghiệp.*
