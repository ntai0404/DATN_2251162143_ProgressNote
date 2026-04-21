# Kịch bản Kiểm thử Giai đoạn Tuần 3-5

## 1. Kiểm thử Tác nhân Thu thập (Collector Agent)
| Case ID | Tên kịch bản | Kết quả mong đợi |
| :--- | :--- | :--- |
| **TC-01** | Đăng nhập & Lọc danh mục HCTLU | Lấy được danh sách văn bản dù portal yêu cầu Login. |
| **TC-02** | Xử lý OCR PDF bản quét | Bóc tách được nội dung Điều/Khoản từ file PDF 27MB. |
| **TC-03** | Tách đoạn Article-level | File JSON đầu ra phải phân cấp rõ ràng theo các Điều luật. |
| **TC-04** | Tránh trùng lặp dữ liệu | File đã tải và xử lý rồi sẽ không được xử lý lại (Check Hash). |

## 2. Kiểm thử Tác nhân Tra cứu (Search Agent)
| Case ID | Tên kịch bản | Kết quả mong đợi |
| :--- | :--- | :--- |
| **TC-05** | Đồng bộ dữ liệu qua RabbitMQ | Khi Collector đẩy tin nhắn, Search Agent phải nhận được ngay. |
| **TC-06** | Tạo điểm Vector trên Qdrant | Kiểm tra Dashboard Qdrant thấy số lượng Points tăng lên tương ứng. |
| **TC-07** | Kiểm thử Search API thô | Truy vấn "học bổng" phải trả về các đoạn luật chứa từ khóa liên quan. |

## 3. Kiểm thử Hạ tầng Cloud-native
| Case ID | Tên kịch bản | Kết quả mong đợi |
| :--- | :--- | :--- |
| **TC-08** | Build Docker Image | Tất cả các service (Collector, Search) build thành công, không lỗi thư viện. |
| **TC-09** | Liên lạc nội bộ trên K8s | Collector có thể "thấy" RabbitMQ và Postgres trong Cluster để gửi dữ liệu. |

## 4. Tiêu chí đạt (Definition of Done - Tuần 5)
- [ ] 100% văn bản quy chế chính (Quy chế đào tạo, Công tác SV) đã được đưa vào Vector DB.
- [ ] Search API hoạt động ổn định với độ trễ < 500ms.
- [ ] Dữ liệu bóc tách không bị lỗi font tiếng Việt.
