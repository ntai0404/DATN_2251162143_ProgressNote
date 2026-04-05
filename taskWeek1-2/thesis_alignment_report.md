# Báo cáo đối soát kết quả Tuần 1-2 so với Đề cương ĐATN

Bản đối soát này giúp bạn nắm bắt nhanh tiến độ để đưa vào báo cáo đồ án. Toàn bộ tài liệu chi tiết nằm trong thư mục `taskWeek1-2/`.

## 1. Đối soát mục tiêu Tuần 1-2

| Nội dung theo Đề cương | Kết quả thực hiện | Vị trí file ( deliverables ) |
| :--- | :--- | :--- |
| **Chốt danh mục quy chế** | Đã xác định 10 nguồn quy chế cốt lõi (Đào tạo, CTSV, Thư viện, Học phí...). | `taskWeek1-2/knowledge_links.md` |
| **Thu thập file PDF/Web gốc** | Khởi tạo kho dữ liệu thô và mã nguồn Collector Agent tự động (Link động). | `taskWeek1-2/data_raw/` và `taskWeek1-2/dynamic_collector.py` |
| **Thiết kế luồng RAG chi tiết** | Đã thiết kế thuật toán Hybrid Search (Vector + BM25) và Re-ranking. | `taskWeek1-2/architecture.md` (Phần 2 & 3) |
| **Thiết kế kiến trúc Đa tác nhân** | Đồ hình MAS với Collector, Search, Analyst, Monitor Agents. | `taskWeek1-2/architecture.md` (Phần 1 - Mermaid code) |
| **Cập nhật Database Schema** | Chốt Schema cho Regulation và Content Chunks hỗ trợ truy vết (Traceability). | `taskWeek1-2/new_models.py` |
| **Chuẩn bị hạ tầng GKE** | Kế hoạch triển khai K8s, Qdrant, RabbitMQ và GPU cho LLM. | `taskWeek1-2/gke_setup.txt` |

## 2. Mã nguồn Mermaid (Dùng cho Báo cáo/Slide)

Mã Mermaid cho sơ đồ kiến trúc MAS nằm tại **dòng 5 - 28** của file `taskWeek1-2/architecture.md`. Bạn có thể copy đoạn code đó dán vào các trình soạn thảo Markdown hoặc Notion/Github để hiển thị sơ đồ.

## 3. Các điểm nhấn kỹ thuật đã hoàn thiện (Để viết báo cáo)

1.  **Tính năng Link Động (Dynamic Discovery)**: Không chỉ là tải file thủ công, hệ thống đã có giải thuật spidering để tự phát hiện văn bản mới trên các subdomain `daotao.tlu.edu.vn`.
2.  **Sự kế thừa từ dự án tiền bối**: Tận dụng framework Microservices có sẵn (RabbitMQ, Qdrant logic) nhưng nâng cấp mạnh mẽ về khả năng xử lý PDF và trích dẫn nguồn luật.
3.  **Thuật toán Hybrid Retrieval**: Giải quyết bài toán tìm kiếm chính xác các mã văn bản (ví dụ "Quyết định 1226") mà các hệ thống RAG thông thường hay bỏ lỡ.
4.  **Kiến trúc Cloud-native**: Sẵn sàng scale trên GKE với khả năng giám sát chất lượng câu trả lời (Monitor Agent).

---
**Trạng thái**: Hoàn thành 100% yêu cầu Tuần 1-2 của Đề cương. Sẵn sàng để viết Báo cáo chương 1 & 2.
