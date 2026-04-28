import os
import time
from playwright.sync_api import sync_playwright
from pathlib import Path

# Storage
BASE_DIR = Path(os.getcwd())
DOWNLOAD_DIR = BASE_DIR / "data_raw"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# TVPL Credentials
TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"

def download_tvpl_word():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Logging into TVPL...")
        try:
            page.goto("https://thuvienphapluat.vn/page/login.aspx", timeout=60000, wait_until="domcontentloaded")
            page.fill("#UserName", TVPL_USER)
            page.fill("#Password", TVPL_PASS)
            page.click("#Button1")
            
            page.wait_for_timeout(3000)
            # Use ASCII only selectors or text-free selectors
            overlap_btn = page.query_selector("input[value='Dong y'], #btnDongY, button:has-text('Dong y')")
            if not overlap_btn:
                # Fallback to broad check
                overlap_btn = page.evaluate("() => Array.from(document.querySelectorAll('input,button')).find(el => el.value === 'Đồng ý' || el.innerText.includes('Đồng ý'))")
            
            if overlap_btn:
                print("Found overlap popup.")
                page.evaluate("() => { const el = Array.from(document.querySelectorAll('input,button')).find(el => el.value === 'Đồng ý' || el.innerText.includes('Đồng ý')); if(el) el.click(); }")
            
            # Navigate to document page
            target_url = "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-08-2021-TT-BGDDT-Quy-che-dao-tao-trinh-do-dai-hoc-470013.aspx"
            print(f"Navigating to document...")
            try:
                page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            except:
                print("Navigation state unclear but proceeding...")

            # Click Download tab
            print("Locating Download tab...")
            tab_download = page.query_selector("a[href*='tab=7']")
            if tab_download:
                tab_download.click()
                page.wait_for_timeout(3000)
            else:
                print("Using direct tab URL...")
                page.goto(target_url + "?tab=7", timeout=30000, wait_until="domcontentloaded")

            # Final download search
            print("Searching for part=-1 link...")
            download_link = page.query_selector("a[href*='part=-1']")
            if download_link:
                print("Starting download...")
                with page.expect_download() as download_info:
                    download_link.click()
                download = download_info.value
                file_path = DOWNLOAD_DIR / "thong_tu_08_2021.doc"
                download.save_as(file_path)
                print(f"SUCCESS: Saved to {file_path}")
                return file_path
            else:
                print("No part=-1 link found.")
                page.screenshot(path="debug_final.png")
                
        except Exception as e:
            # Avoid printing error message directly if it contains unicode
            print(f"An error occurred during process.")
        finally:
            browser.close()

if __name__ == "__main__":
    download_tvpl_word()
