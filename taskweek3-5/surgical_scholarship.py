import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
PASS = os.getenv("HANH_CHINH_TLU_PASS", "123456")

def harvest_scholarships():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print("Logging into HCTLU...")
        page.goto("http://hanhchinh.tlu.edu.vn/login.aspx")
        page.fill("#txtUser", USER)
        page.fill("#txtPass", PASS)
        page.click("#btnLogin")
        page.wait_for_load_state("networkidle")
        
        print("Searching for 'học bổng'...")
        # Navigate to document search or main repo
        page.goto("http://hanhchinh.tlu.edu.vn/VanBanDieuHanh.aspx")
        page.fill("#txtSearch", "học bổng")
        page.click("#btnSearch")
        time.sleep(5)
        
        # Extract all PDF links
        links = page.query_selector_all("a[href*='.pdf']")
        print(f"Found {len(links)} potential scholarship links.")
        
        os.makedirs("data_raw", exist_ok=True)
        
        for i, link in enumerate(links):
            try:
                href = link.get_attribute("href")
                title = link.inner_text().strip() or f"scholarship_{i}"
                if not href.startswith("http"):
                    href = "http://hanhchinh.tlu.edu.vn/" + href
                
                print(f"Downloading: {title} from {href}")
                # Use download handler or simple request
                with page.expect_download() as download_info:
                    link.click()
                download = download_info.value
                path = os.path.join("data_raw", f"{title}.pdf")
                download.save_as(path)
                print(f"Saved to {path}")
            except Exception as e:
                print(f"Failed to download {i}: {e}")
                
        browser.close()

if __name__ == "__main__":
    harvest_scholarships()
