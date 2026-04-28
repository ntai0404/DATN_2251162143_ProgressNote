import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

load_dotenv()

class WebScraper:
    def __init__(self):
        self.tvpl_user = os.getenv("THU_VIEN_PHAP_LUAT_USER")
        self.tvpl_pass = os.getenv("THU_VIEN_PHAP_LUAT_PASS")
        self.hctlu_user = os.getenv("HANH_CHINH_TLU_USER")
        self.hctlu_pass = os.getenv("HANH_CHINH_TLU_PASS")

    def login_thuvienphapluat(self, page):
        print("Logging in to Thư viện pháp luật...")
        page.goto("https://thuvienphapluat.vn/page/login.aspx")
        page.fill("#UserName", self.tvpl_user)
        page.fill("#Password", self.tvpl_pass)
        page.click("#Button1")
        page.wait_for_load_state("networkidle")
        print("Logged in to Thư viện pháp luật.")

    def login_hanhchinh_tlu(self, page):
        print("Logging in to Hành chính TLU...")
        page.goto("http://hanhchinh.tlu.edu.vn/")
        try:
            page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", self.hctlu_user)
            page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", self.hctlu_pass)
            page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
            page.wait_for_load_state("networkidle")
            print("Logged in to Hành chính TLU.")
        except Exception as e:
            print(f"Failed to login to Hành chính TLU: {e}")

    def scrape_tlu_news(self, url="https://tlu.edu.vn/tin-tuc-thong-bao/tin-tuc/"):
        print(f"Scraping TLU News from {url}...")
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")
            
            # Updated selectors based on live discovery
            items = page.locator(".post-item").all()
            for item in items:
                # The entire item is a link or contains a link
                link_elem = item.locator("a").first
                if link_elem.count() > 0:
                    title = item.inner_text().split("\n")[0].strip()
                    link = link_elem.get_attribute("href")
                    
                    results.append({
                        "title": title,
                        "url": link,
                        "content": title, # Placeholder
                        "metadata": {"source": "tlu_news", "level": 5}
                    })
            browser.close()
        return results

    def download_file(self, page, selector, filename):
        """
        Download a file by clicking a link/button using Playwright's download handler.
        """
        import os
        download_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_downloads"
        save_path = os.path.join(download_dir, filename)
        
        try:
            with page.expect_download() as download_info:
                page.click(selector)
            download = download_info.value
            download.save_as(save_path)
            print(f"DOWNLOAD SUCCESS: {filename} ({os.path.getsize(save_path)} bytes)")
            return save_path
        except Exception as e:
            print(f"Download failed for {selector}: {e}")
        return None

    def extract_portal_documents(self, page, portal_name):
        print(f"Extracting and downloading documents from {portal_name}...")
        # Targeted selectors for DNN portals or TVPL
        selectors = [
            "a[href*='.pdf']", 
            "a[href*='Download']",
            "a.download-link",
            "span.fa-download" # Some icons are clickable
        ]
        
        extracted = []
        for selector in selectors:
            elements = page.locator(selector).all()
            for i, el in enumerate(elements[:3]): # Limit per type for demo
                try:
                    text = el.inner_text().strip() or f"Doc_{i}"
                    safe_name = "".join([c for c in text if c.isalnum() or c in (' ', '_', '-')]).strip()[:50]
                    filename = f"{portal_name}_{safe_name}_{int(time.time())}.pdf"
                    
                    local_path = self.download_file(page, f"{selector} >> nth={i}", filename)
                    
                    if local_path:
                        extracted.append({
                            "title": text,
                            "url": page.url,
                            "local_path": local_path,
                            "type": "pdf_ingested",
                            "metadata": {"source": portal_name, "level": 5}
                        })
                except Exception as e:
                    print(f"Skipping element: {e}")
                    
        return extracted

if __name__ == "__main__":
    scraper = WebScraper()
    # scraper.scrape_tlu_news()
    print("WebScraper initialized. Ready to scrape.")
