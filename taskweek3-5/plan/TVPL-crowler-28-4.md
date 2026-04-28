# BÁO CÁO KIẾN TRÚC VÀ VẬN HÀNH: TVPL MINI-COLLECTOR (28/04/2026)

*Báo cáo kỹ thuật dành cho đội ngũ phát triển Backend, OCR và Quản trị Hệ thống.*

---

## 1. KHẢO SÁT ĐẦU VÀO (SOURCE ANALYSIS: THUVIENPHAPLUAT.VN)
Trước khi xây dựng Crawler, việc khảo sát chuyên sâu mục tiêu (trang Thư Viện Pháp Luật - TVPL) đã làm bộc lộ các đặc thù và khó khăn của nguồn dữ liệu này:
- **Cơ chế bảo mật (Anti-Bot):** TVPL sử dụng Cloudflare để quét fingerprint của trình duyệt. Nếu phát hiện các tool tự động (Selenium, Puppeteer thông thường), nó sẽ chặn hoặc trả về Captcha.
- **Phân quyền truy cập:** Tài khoản khách (Guest) chỉ xem được một phần văn bản. Để tải hoặc xem Full Text, bắt buộc phải có phiên đăng nhập (Login Session) hợp lệ.
- **Cấu trúc DOM lộn xộn, thiếu chuẩn hóa:** TVPL được xây dựng từ lâu, mã nguồn HTML rất tạp nham. Khối chứa nội dung văn bản (`div.content1`) bị nhồi nhét rất nhiều CSS nội tuyến (`style="..."`), thẻ `<script>` quảng cáo, và thẻ iframe.
- **Metadata không đồng nhất:** Các thẻ như "Tình trạng hiệu lực", "Ngày ban hành" không có id hay class cố định. Có văn bản dùng thẻ `<table>`, có văn bản dùng thẻ `<font>` hoặc `<div>` xếp chồng lên nhau.
- **URL bị loãng:** Một văn bản có thể được truy cập bằng nhiều URL khác nhau do dính query string (ví dụ: `?tab=7`, `&keyword=luat`). Nếu không cẩn thận sẽ cào trùng 1 văn bản hàng chục lần.

---

## 2. TỔNG QUAN VÀ CẤU TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)
Để giải quyết bài toán trên, **TVPL Harvester** được thiết kế thành một Mini-Service gọn gàng, hoạt động độc lập (Decoupled) nằm bên trong thư mục của Collector Agent.

**Cấu trúc thư mục lõi:**
```text
collector_agent/services/tvpl_harvester/
├── __init__.py        
├── config.py          # Lưu thông tin Credentials, Link mồi, Keywords, Cấu hình Browser.
├── browser.py         # Quản lý trình duyệt (Playwright), vượt rào Anti-bot, xử lý Auto-Login & Session.
├── extractor.py       # Tách bóc DOM: Rửa sạch HTML, dùng Regex trích xuất Metadata, bọc lại thành YAML.
├── spider.py          # Não bộ điều hướng (BFS Queue), kiểm tra trùng lặp URL, nhớ trạng thái vào JSON.
└── harvester.py       # Khung sườn (Facade) gom Browser, Extractor và Spider lại thành 1 pipeline chạy duy nhất.
```

**Triết lý thiết kế:** Plug & Play (Cắm và Chạy). Hoạt động không can thiệp hay làm gián đoạn luồng xử lý PDF nội bộ (OCR) của Đại học Thủy Lợi, nhưng định dạng đầu ra (`.md` kèm YAML) hoàn toàn tương thích với hệ thống Chunking của RAG.

---

## 3. THƯ VIỆN CÔNG NGHỆ (TECH STACK)
Hệ thống sử dụng các thư viện tối ưu hóa cho bài toán cào dữ liệu động và xử lý văn bản:
- **`playwright`**: Trình duyệt không đầu (Headless Browser) mạnh mẽ nhất hiện nay, dùng để render Javascript, giải quyết các nội dung tải động.
- **`playwright-stealth`**: Công cụ "tàng hình" vượt qua lớp bảo mật chống Bot.
- **`beautifulsoup4` (BS4)**: Phân tích và điều hướng cây DOM HTML.
- **`markdownify`**: Trình biên dịch ngược từ HTML sang định dạng Markdown.
- **`logging.handlers.RotatingFileHandler`**: Hệ thống ghi log chuẩn Microservice chống tràn ổ cứng.

---

## 4. QUY TRÌNH LẤY VÀ XỬ LÝ DỮ LIỆU
Tiến trình cào diễn ra qua 2 giai đoạn (Phases):
1. **Phase 1 (Priority Harvest):** Cào cứng 7 tài liệu luật nền tảng được định nghĩa sẵn.
2. **Phase 2 (Discovery):** Cào mở rộng theo thuật toán BFS (Breadth-First Search). Quét các link liên kết trên trang vừa cào, nếu thỏa mãn `DISCOVERY_KEYWORDS` thì nạp vào hàng đợi.

**Luồng xử lý (Data Pipeline):**
- **DOM Cleaning:** Bóc chính xác thẻ `<div class="content1">`. Xóa toàn bộ CSS nội tuyến (`style="..."`), xóa các class thừa, thẻ `<script>`, `<iframe>`.
- **Metadata Extraction:** Bóc tách tiêu đề, tình trạng hiệu lực, ngày ban hành để tạo **YAML Frontmatter** dán lên đầu file `.md`.
- **Markdown Conversion & Smart Join:** Chuyển HTML sang Markdown bằng `markdownify`. Kèm theo thuật toán nội bộ `_smart_join` để nối các câu pháp luật bị rớt dòng do lỗi thiết kế web của TVPL, bảo toàn toàn vẹn ngữ nghĩa.
- **Decoupled Ingestion:** Lưu trữ file thô vào `data_raw/tvpl/*.md` an toàn tuyệt đối trước khi nạp vào Vector DB (Qdrant).

---

## 5. RÀO CẢN KỸ THUẬT VÀ PHƯƠNG PHÁP VƯỢT RÀO
| Rào cản (Blockers) | Phương pháp giải quyết (Solutions) |
| --- | --- |
| **TVPL có hệ thống Anti-bot** | Dùng `playwright-stealth` tiêm kịch bản ngụy trang fingerprint, giả lập user-agent của trình duyệt người thật. |
| **Bắt buộc đăng nhập** | Lập trình bot tự động điền Username/Password, click đăng nhập (`_do_login`) để lấy quyền xem Full Text. |
| **Session/Cookie hết hạn** | Thuật toán **Khám sức khỏe Session** (`_is_session_alive`). Nếu bị đá văng khỏi hệ thống, bot tự động xin cấp Session mới và ghi đè file `.tvpl_session.json`. |
| **HTML không đồng nhất** | Chuyển từ "Cào bằng Selector cứng" sang "Cào bằng Regex nhãn (Label-based Regex)". Tìm chữ "Tình trạng:" rồi bóc nội dung kế bên, bất chấp thẻ HTML bên ngoài. |
| **Ngộ độc URL rác** | Cơ chế **URL Normalization**. Cắt bỏ sạch các query string (như `?tab=`) trước khi đưa vào hàng chờ kiểm tra trùng lặp. |

---

## 6. CƠ CHẾ CHỐNG LỖI (FAULT-TOLERANCE)
Hệ thống được thiết kế theo triết lý "Fail-soft" của Microservice:
- **Nhớ trạng thái (State Persistence):** Sử dụng file `tvpl_spider_state.json` lưu giữ chính xác tiến độ cào. Sập nguồn hay tắt điện, lần sau mở lên chạy tiếp đoạn đó, không cào lại từ đầu.
- **Re-queue (Vòng lặp sửa sai):** Bọc `try-catch` vào từng request tải trang. Nếu đứt mạng / Timeout, URL đó không bị vứt bỏ mà được nhét ngược xuống cuối hàng chờ để thử lại.
- **Log Monitoring:** Ghi log có cấu trúc rõ ràng: `Thời gian \| Tên Module \| [Mức độ] \| Tin nhắn`. Đổ vào file `tvpl_collector.log` qua cơ chế xoay vòng (Rotating) giới hạn 5MB/file, giữ 3 bản sao để chống tràn disk.
- **Isolation (Cô lập lỗi):** Lỗi của dịch vụ Qdrant VectorDB (nếu đang tắt) sẽ không làm ảnh hưởng đến tiến trình Spider. Crawler vẫn cào thành công và lưu file `.md` an toàn vào ổ cứng.

---

## 7. KIM CHỈ NAM CHUYỂN GIAO (GUIDELINES FOR FUTURE DEVS)
Để giữ vững kiến trúc chuẩn mực (Enterprise-grade) của toàn bộ dự án DATN khi phát triển các Agent/Service tiếp theo (Search, Ingestion, OCR...), team cần tuân thủ 5 nguyên tắc sau:

1. **Nguyên tắc "Tách rời và Đệm" (Decoupling & Buffering):**
   - Không nạp thẳng dữ liệu cào/OCR được vào VectorDB ngay lập tức. Luôn lưu ra ổ cứng (Local Storage / Buffer) trước. Nếu Qdrant sập, Agent thu thập vẫn sống khỏe và bảo toàn được dữ liệu.

2. **Thiết kế phần mềm kiểu "Sập lúc nào cũng được" (Crash-only Design):**
   - Với các tác vụ chạy ngầm lâu (Long-running tasks), **phải luôn có State Persistence**. Giả định rằng máy chủ có thể mất điện. Khi khởi động lại, Agent phải tự biết đọc file State (VD: JSON, SQLite) để chạy tiếp đoạn dang dở, không làm lại từ đầu.

3. **Nói KHÔNG với lệnh `print()`:**
   - Trong kiến trúc Multi-Agent, bắt buộc dùng hệ thống Log chuẩn (`logging` với `RotatingFileHandler`). Luôn gắn tag Tên Module vào Log để dễ trace lỗi. Không dùng `print()` bừa bãi.

4. **Metadata quan trọng ngang bằng Nội dung:**
   - Dữ liệu thô (Raw text) chỉ giải quyết Semantic Search. Để làm **Hybrid Search** chính xác tuyệt đối, phải trích xuất được Metadata (YAML Frontmatter) làm "Bộ lọc" (Filter) cứng.

5. **Dùng "Facade Pattern" che giấu sự phức tạp:**
   - Dù logic ngầm phức tạp đến đâu, hãy tạo một lớp Facade đơn giản để các Orchestrator gọi đến bằng 1-2 dòng code. Giữ cho hệ thống luôn "Plug & Play".
