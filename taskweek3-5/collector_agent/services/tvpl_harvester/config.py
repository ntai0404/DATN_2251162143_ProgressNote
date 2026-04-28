"""
tvpl_harvester/config.py
========================
Cấu hình trung tâm cho TVPL Harvester.
- PRIORITY_URLS: 7 văn bản BẮT BUỘC phải có, được collect trước tiên.
- Credentials và constants tập trung ở đây để dễ update.
"""

# --- Credentials ---
TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"
TVPL_BASE_URL = "https://thuvienphapluat.vn"

# --- 7 Văn bản ưu tiên (collect cứng trước) ---
# ⚠️ Khi cần thêm/thay URL, chỉ cần sửa list này — không cần đụng code khác.
PRIORITY_URLS = [
    # [1] Luật Giáo dục 2019 (bản hiện hành)
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-367665.aspx",
    # [2] Luật Giáo dục Đại học 2012 (đã sửa đổi 2018)
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-Giao-duc-dai-hoc-2012-142762.aspx",
    # [3] Quy chế công tác sinh viên (Thông tư 10/2016)
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-10-2016-TT-BGDDT-quy-che-cong-tac-sinh-vien-chuong-trinh-dao-tao-dai-hoc-he-chinh-quy-308413.aspx",
    # [4] Luật Cán bộ Công chức 2008 (đã bao gồm sửa đổi 2019) ✓ verified
    "https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-can-bo-cong-chuc-2008-22-2008-QH12-82202.aspx",
    # [5] Luật Viên chức 2010 (đã bao gồm sửa đổi 2019) ✓ verified
    "https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-vien-chuc-2010-115271.aspx",
    # [6] Nghị định 84/2020/NĐ-CP hướng dẫn Luật Giáo dục 2019 ✓ verified
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Nghi-dinh-84-2020-ND-CP-huong-dan-Luat-Giao-duc-447674.aspx",
    # [7] Nghị định 99/2019/NĐ-CP hướng dẫn Luật GDĐH sửa đổi ✓ verified
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Nghi-dinh-99-2019-ND-CP-huong-dan-thi-hanh-Luat-Giao-duc-dai-hoc-sua-doi-432145.aspx",
]

# --- Keywords để lọc link trong Spider (mở rộng sau Priority) ---
DISCOVERY_KEYWORDS = [
    "giao-duc", "dao-tao", "sinh-vien", "hoc-sinh", "nha-giao",
    "hoc-bong", "tuyen-sinh", "cong-chuc", "vien-chuc", "quy-che",
    "hoc-phi", "bang-cap", "chung-chi",
]

# --- Thresholds ---
MIN_CONTENT_LENGTH = 500   # chars — bỏ qua nếu nội dung quá ngắn
SPIDER_DELAY_MIN   = 3.0   # seconds — delay tối thiểu giữa 2 request
SPIDER_DELAY_MAX   = 7.0   # seconds — delay tối đa
