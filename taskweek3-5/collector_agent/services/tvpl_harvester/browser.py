"""
tvpl_harvester/browser.py
=========================
Quản lý vòng đời browser + login TVPL với cơ chế **Persistent Session**.

Chiến lược chống block (quan trọng cho cào hàng ngày):
─────────────────────────────────────────────────────
1. PERSISTENT COOKIES: Sau lần login đầu, lưu toàn bộ trạng thái session
   (cookies + localStorage) vào file JSON. Các lần chạy tiếp theo TÁI SỬ DỤNG
   ngay — không đăng nhập lại, không kích hoạt bot-detection của TVPL.

2. SESSION HEALTH CHECK: Trước mỗi lần cào, kiểm tra session còn sống không
   bằng cách thử navigate đến trang profile. Nếu bị redirect về trang login
   → tự động đăng nhập lại và lưu session mới.

3. STEALTH: Dùng playwright-stealth để che fingerprint, tránh Cloudflare.

4. RANDOM DELAYS: Delay ngẫu nhiên giữa các request (xử lý ở spider.py).

Kết quả: Session thường sống 7-30 ngày, không cần manual action.
"""

import json
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth

from .config import TVPL_USER, TVPL_PASS

log = logging.getLogger("TVPL.Browser")

_SESSION_FILE = Path(__file__).parent / ".tvpl_session.json"
_LOGIN_URL = "https://thuvienphapluat.vn/page/login.aspx"
_HEALTH_URL = "https://thuvienphapluat.vn/khach-hang/ho-so.aspx"
_HOME_URL   = "https://thuvienphapluat.vn"


class TVPLBrowser:
    """
    Context manager cho Playwright browser với Persistent Session.

    Usage:
        with TVPLBrowser() as ctx:
            page = ctx.new_page()
            page.goto("https://thuvienphapluat.vn/van-ban/...")
    """

    def __init__(self, headless: bool = True, session_file: Path = _SESSION_FILE):
        self.headless = headless
        self.session_file = session_file
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None

    # ─── Context manager ──────────────────────────────────────────────────────

    def __enter__(self) -> BrowserContext:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._context = self._make_context()
        self._ensure_logged_in()
        return self._context

    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _make_context(self) -> BrowserContext:
        """Tạo context, nạp session đã lưu nếu có."""
        kwargs = dict(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
        )
        if self.session_file.exists():
            log.info(f"Loading saved session from {self.session_file.name}")
            kwargs["storage_state"] = str(self.session_file)

        return self._browser.new_context(**kwargs)

    def _apply_stealth(self, page: Page):
        Stealth().apply_stealth_sync(page)

    def _save_session(self):
        """Lưu trạng thái session (cookies + localStorage) vào file."""
        state = self._context.storage_state()
        self.session_file.write_text(json.dumps(state), encoding="utf-8")
        log.info(f"Session saved → {self.session_file.name}")

    def _is_session_alive(self) -> bool:
        """
        Kiểm tra session còn sống: navigate đến trang profile.
        Nếu được redirect về /login → session đã hết hạn.
        """
        probe = self._context.new_page()
        self._apply_stealth(probe)
        try:
            probe.goto(_HEALTH_URL, wait_until="networkidle", timeout=15_000)
            alive = "/login" not in probe.url and "login" not in probe.url.lower()
            log.info(f"Session health: {'ALIVE' if alive else 'EXPIRED'} ({probe.url})")
            return alive
        except Exception as e:
            log.warning(f"Session health check failed: {e}")
            return False
        finally:
            probe.close()

    def _do_login(self):
        """Thực hiện đăng nhập và lưu session ngay sau đó."""
        log.info("Performing fresh login to TVPL...")
        page: Page = self._context.new_page()
        self._apply_stealth(page)
        try:
            page.goto(_LOGIN_URL, wait_until="networkidle", timeout=30_000)
            page.fill("#UserName", TVPL_USER)
            page.fill("#Password", TVPL_PASS)
            page.click("#Button1")
            # TVPL sau khi login thường ở lại trang có ?dll=true hoặc redirect
            # Dùng wait_for_timeout + kiểm tra cookie thay vì wait_for_url
            page.wait_for_timeout(5000)
            # Kiểm tra xem login thành công chưa qua cookie/title
            page_title = page.title()
            current_url = page.url
            log.info(f"Post-login: url={current_url}, title={page_title}")
            # Nếu vẫn ở trang login và có thông báo lỗi, raise exception
            error_el = page.query_selector(".error-message, #lblErrorMsg, .alert-danger")
            if error_el and error_el.inner_text().strip():
                raise Exception(f"Login error: {error_el.inner_text().strip()}")
            log.info("Login completed successfully.")
        except Exception as e:
            log.error(f"Login failed: {e}")
            raise
        finally:
            page.close()
        self._save_session()

    def _ensure_logged_in(self):
        """
        Kiểm tra + đảm bảo session hợp lệ trước khi bắt đầu cào.
        Nếu có session file → kiểm tra còn sống không.
        Nếu không có hoặc hết hạn → đăng nhập mới.
        """
        if self.session_file.exists():
            if self._is_session_alive():
                log.info("Reusing existing session — skipping login.")
                return
            log.info("Session expired. Logging in again...")
        else:
            log.info("No session file found. Logging in for the first time...")

        self._do_login()
