# BÁO CÁO CẬP NHẬT: PHÂN TÍCH LỖI RETRIEVAL & OCR (WEEK 3-5)

Tôi đã thực hiện kiểm tra sâu (forensic audit) hệ thống và xác định 3 nguyên nhân cốt lõi khiến kết quả tra cứu "cấp học bổng" bị sai lệch.

## 1. Thiếu dữ liệu (Nguyên nhân chính)
Hệ thống trả về kết quả không liên quan vì **Văn bản quy định về Học bổng chưa có trong kho dữ liệu 121 file đã cào.**
- **Kiểm chứng:** Tôi đã chạy script scan toàn bộ nội dung text (First-layer scan) của 121 file PDF hiện có, kết quả xác nhận không có file nào chứa từ khóa "học bổng".
- **Lý do:** Cơ chế "Vét TabID" ban đầu đã bỏ sót phân mục Học bổng trên portal HCTLU (có thể do phân mục này nằm ở dải ID khác hoặc yêu cầu quyền truy cập đặc thù hơn).

## 2. Lỗi Font & Trích xuất (OCR/Extraction Error)
Như anh thấy ở Trích dẫn 2 (`phen. 2T $u t.or eiirrl.e ifuogg`), văn bản bị lỗi font nghiêm trọng.
- **Nguyên nhân:** File "Quy định khảo sát ý kiến" trên HCTLU được lưu dưới dạng PDF scan chất lượng thấp hoặc sử dụng bảng mã font không chuẩn (Non-standard encoding). 
- **Hệ quả:** Thư viện `PyMuPDF` không thể map sang mã Unicode chuẩn, dẫn đến dữ liệu đưa vào Vector DB là "rác" (Garbage data), làm giảm độ chính xác khi đối sánh ngữ nghĩa.

## 3. Cơ chế Fallback của AI (Độ chính xác thấp)
Tại sao không có dữ liệu học bổng mà AI vẫn trả về "Chi tiêu nội bộ"?
- Khi không tìm thấy kết quả khớp 100%, Search Agent sẽ lấy các đoạn văn bản có **tọa độ vector gần nhất**. 
- Quy chế chi tiêu nội bộ có chứa các từ khóa liên quan đến "tài chính", "nguồn tiền", "sinh viên" nên AI hiểu nhầm đây là nội dung gần nhất với "cấp học bổng". Tuy nhiên độ tin cậy chỉ đạt 0.42 (Rất thấp).

---

## Kế hoạch khắc phục (Action Plan):
1. **Surgical Harvest (Cào bổ sung):** Tôi sẽ dùng Playwright để đăng nhập và tìm kiếm chính xác từ khóa "học bổng" trên giao diện Tra cứu của HCTLU để lấy link trực tiếp, không phụ thuộc vào TabID.
2. **Re-ingestion:** Sau khi có file chuẩn, tôi sẽ xử lý lại (Ingest) để nạp vào Qdrant.
3. **OCR Improvement:** Với các file bị lỗi font, tôi sẽ tích hợp giải pháp OCR mạnh hơn (Tesseract hoặc quét lại layer ảnh) để đảm bảo text sạch.

**Tôi báo cáo để anh nắm rõ tình hình trước khi tôi tiến hành sửa code và cào lại dữ liệu.**
