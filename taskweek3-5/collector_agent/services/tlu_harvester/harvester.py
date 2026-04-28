import logging
import re
from pathlib import Path
from playwright.sync_api import Page, BrowserContext
from playwright_stealth import Stealth

from .config import DEFAULT_TABS, PLAYWRIGHT_HEADLESS
from .browser import TLUBrowser

log = logging.getLogger("Collector.TLU.Harvester")

class TLUHarvester:
    """
    TLUHarvester - Thu thập văn bản quy phạm từ Portal Hành chính TLU.
    """
    def __init__(self, output_dir: Path, headless: bool = PLAYWRIGHT_HEADLESS):
        self.output_dir = output_dir
        self.headless = headless
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, max_pages: int = None) -> list[Path]:
        """
        Chạy quy trình thu thập từ các Tab mặc định.
        Args:
            max_pages: Nếu None sẽ cào sạch đến trang cuối.
        """
        downloaded_files = []
        
        with TLUBrowser(headless=self.headless) as ctx:
            for url in DEFAULT_TABS:
                log.info(f"Harvesting TLU Tab: {url}")
                files = self._harvest_tab(ctx, url, max_pages)
                downloaded_files.extend(files)
                
        return downloaded_files

    def _harvest_tab(self, context: BrowserContext, url: str, max_pages: int) -> list[Path]:
        tab_files = []
        page: Page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            page.goto(url, timeout=60000, wait_until="networkidle")
            
            current_page_num = 1
            while True:
                log.info(f"  TLU Page {current_page_num}")
                
                grid_selector = "table[id*='grdDocuments']"
                try:
                    page.wait_for_selector(grid_selector, timeout=15000)
                except:
                    log.warning("    Grid not found, stopping this tab.")
                    break

                rows = page.query_selector_all(f"{grid_selector} tr")
                for row in rows:
                    link_el = row.query_selector("a[href*='LinkClick']")
                    if not link_el: continue
                    
                    cells = row.query_selector_all("td")
                    if len(cells) < 2: continue
                        
                    title = cells[1].inner_text().strip()
                    if not title: continue
                    
                    file_path = self._download_file(page, link_el, title)
                    if file_path:
                        tab_files.append(file_path)

                # Pagination - Cào đến khi không còn nút Next
                next_btn = page.query_selector(f"tr.PagerStyle a:has-text('{current_page_num + 1}')")
                
                if next_btn and (max_pages is None or current_page_num < max_pages):
                    log.info(f"    Moving to page {current_page_num + 1}...")
                    next_btn.click()
                    page.wait_for_timeout(3000)
                    current_page_num += 1
                else:
                    log.info("    Reached last page or limit.")
                    break
                    
        except Exception as e:
            log.error(f"Error in TLU tab harvest: {e}")
        finally:
            page.close()
            
        return tab_files

    def _download_file(self, page: Page, link_el, title: str) -> Path | None:
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:100]
        
        try:
            # Tăng timeout lên 90s cho các file nặng
            with page.expect_download(timeout=90000) as download_info:
                link_el.click()
            
            download = download_info.value
            ext = Path(download.suggested_filename).suffix or ".pdf"
            final_path = self.output_dir / f"{safe_title}{ext}"
            
            # Deduplication: Chỉ skip nếu file đã tồn tại và "khỏe mạnh" (>1KB)
            if final_path.exists() and final_path.stat().st_size > 1024:
                log.debug(f"    Skip existing healthy file: {final_path.name}")
                return final_path
                
            download.save_as(final_path)
            
            # Kiểm tra tính toàn vẹn (Integrity Check) sau khi lưu
            if final_path.stat().st_size < 1024:
                log.warning(f"    ⚠️ File quá nhỏ ({final_path.stat().st_size} bytes), có thể bị lỗi: {final_path.name}")

            log.info(f"    ✅ Saved: {final_path.name}")
            return final_path
            
        except Exception as e:
            log.error(f"    ❌ Download failed [{title}]: {e}")
            return None
