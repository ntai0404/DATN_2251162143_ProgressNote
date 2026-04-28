import json
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page
from playwright_stealth import Stealth

from .config import TLU_USER, TLU_PASS, TLU_PORTAL, USER_AGENT, PLAYWRIGHT_HEADLESS

log = logging.getLogger("Collector.TLU.Browser")

_SESSION_FILE = Path(__file__).parent / ".tlu_session.json"

class TLUBrowser:
    """
    Quản lý Browser và Session cho Hành chính TLU Portal.
    Sử dụng Persistent Session để tránh login nhiều lần.
    """
    def __init__(self, headless: bool = PLAYWRIGHT_HEADLESS, session_file: Path = _SESSION_FILE):
        self.headless = headless
        self.session_file = session_file
        self._playwright = None
        self._browser = None

    def __enter__(self) -> BrowserContext:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        kwargs = {
            "user_agent": USER_AGENT,
            "viewport": {"width": 1280, "height": 800},
            "locale": "vi-VN"
        }
        if self.session_file.exists():
            log.info(f"Loading TLU session from {self.session_file.name}")
            kwargs["storage_state"] = str(self.session_file)
            
        self.context = self._browser.new_context(**kwargs)
        self._ensure_login()
        return self.context

    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _ensure_login(self):
        page = self.context.new_page()
        Stealth().apply_stealth_sync(page)
        try:
            log.debug(f"Checking TLU session status...")
            # Navigate to a page that requires login or shows user info
            page.goto(f"{TLU_PORTAL}/Default.aspx?tabid=74", timeout=45000)
            
            content = page.content()
            # Kiểm tra text xác nhận đã đăng nhập (Đỗ Xuân Dũng hoặc nút Đăng xuất)
            if "Đỗ Xuân Dũng" in content or "Logout" in content or "Đăng xuất" in content:
                log.debug("TLU Session is VALID.")
                return

            log.info("TLU Session EXPIRED or missing. Logging in...")
            # Tìm input login
            user_input = page.query_selector("#dnn_ctr_Login_Login_DNN_txtUsername")
            if not user_input:
                page.goto(f"{TLU_PORTAL}/Default.aspx?tabid=74&ctl=Login", timeout=30000)
                user_input = page.wait_for_selector("#dnn_ctr_Login_Login_DNN_txtUsername")

            page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", TLU_USER)
            page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", TLU_PASS)
            page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
            
            page.wait_for_timeout(3000)

            # Xử lý popup đăng nhập trùng (nếu có)
            overlap_btn = page.query_selector("input[value='Đồng ý'], button:has-text('Đồng ý'), #btnDongY")
            if overlap_btn and overlap_btn.is_visible():
                log.info("TLU: Handling concurrent session popup...")
                overlap_btn.click()
                page.wait_for_timeout(3000)
            
            if "Đỗ Xuân Dũng" in page.content() or "Logout" in page.content():
                log.info("TLU Login SUCCESSFUL.")
                state = self.context.storage_state()
                self.session_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            else:
                log.warning("TLU Login might have failed.")
                
        except Exception as e:
            log.error(f"TLU Login error: {e}")
        finally:
            page.close()
