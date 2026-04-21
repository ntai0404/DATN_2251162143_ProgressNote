# Đặc tả Yêu cầu: Collector Agent & Search API (Giai đoạn Tuần 3-5)

## 1. Mục tiêu Giai đoạn (Tuần 3-5)
Hoàn thiện "Hệ thống thần kinh cảm giác" và "Kho tri thức" cho dự án. Mục tiêu là biến hàng trăm file PDF rời rạc trên Portal trường thành một cơ sở dữ liệu Vector có cấu trúc, có thể tra cứu được bằng API.

## 2. Đối tượng sử dụng trong giai đoạn này
- **Nhà phát triển (Sinh viên thực hiện):** Kiểm tra khả năng bóc tách tri thức và tính ổn định của API tra cứu.
- **Cán bộ Nhà trường:** Kiểm tra tính đầy đủ của các văn bản đã được đưa vào kho.

## 3. Các tính năng cốt lõi cần hoàn thiện (Scope Tuần 3-5)

### 3.1. Tác nhân Thu thập (Collector Agent)
- **Thu thập nguồn kép:** Tự động đăng nhập và tải văn bản từ Portal Hành chính TLU và Thư viện Pháp luật (TVPL).
- **Module Xử lý PDF & OCR:** 
    - Nhận diện và trích xuất nội dung từ PDF dạng ảnh quét (scanned).
    - Làm sạch dữ liệu: Loại bỏ header/footer, lỗi font.
- **Cấu trúc hóa tri thức (Article-level Chunking):** 
    - Phải tách đoạn văn bản theo đơn vị **Điều** và **Khoản**.
    - Mỗi đoạn văn bản phải đi kèm metadata: Tên văn bản, đường dẫn PDF gốc, Ngày ban hành.

### 3.2. Tác nhân Tra cứu (Search Agent - Base)
- **Vector Indexing:** Chuyển đổi dữ liệu đã bóc tách thành Vector nhúng (Embedding) và lưu vào Qdrant.
- **Search API lõi:** Phát triển endpoint `/search` để tìm kiếm 5 đoạn văn bản có nội dung sát nhất với câu truy vấn của người dùng.

### 3.3. Hạ tầng và Giám sát (Monitor Agent - Base)
- **Quản lý Meta-DB:** Lưu trữ thông tin metadata của văn bản vào PostgreSQL.
- **Hạ tầng Cloud-native:** Đóng gói tất cả các service thành Docker Image và cấu hình manifest triển khai lên Cluster.

---

## 4. Sản phẩm đầu ra (Kết quả mong đợi mốc Tuần 5)
1.  **Kho tri thức số (Knowledge Base):** Chứa dữ liệu của ~120 văn bản từ TLU và các luật liên quan từ TVPL trên Vector DB.
2.  **API tra cứu hoạt động độc lập:** Cho kết quả nhanh và chính xác về mặt ngữ nghĩa (chưa cần LLM tổng hợp).
3.  **Hệ thống bóc tách PDF:** Hoạt động ổn định trên cả file PDF text và PDF scan.
