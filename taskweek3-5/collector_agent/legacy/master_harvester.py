import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

class MasterHarvester:
    def __init__(self):
        self.user = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
        self.password = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")
        self.download_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw"
        os.makedirs(self.download_dir, exist_ok=True)

    def harvest_hctlu(self):
        print("Starting Aggressive HCTLU Harvest...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            
            # Login
            page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74")
            try:
                page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", self.user)
                page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", self.password)
                page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
                page.wait_for_load_state("networkidle")
                print("HCTLU Login Successful.")
            except:
                print("Already logged in or login failed.")

            # Brute force Tab IDs commonly used for documents
            # Usually 70-130 range in DNN
            target_tabs = [74, 76, 80, 85, 90, 100, 110, 120]
            for tab_id in target_tabs:
                url = f"https://hanhchinh.tlu.edu.vn/Default.aspx?tabid={tab_id}"
                print(f"Scanning Tab {tab_id}: {url}")
                page.goto(url)
                page.wait_for_timeout(3000)
                
                # Discovery: Look for LinkClick or PDF
                links = page.locator("a[href*='LinkClick'], a[href*='.pdf'], a[href*='Download']").all()
                print(f"Found {len(links)} potential links on Tab {tab_id}")
                
                for i, link in enumerate(links[:5]): # Limit to first 5 per tab for safety
                    try:
                        href = link.get_attribute("href")
                        text = link.inner_text().strip() or f"file_{tab_id}_{i}"
                        filename = "".join([c for c in text if c.isalnum() or c in (' ', '_')]).strip()[:30] + ".pdf"
                        save_path = os.path.join(self.download_dir, filename)
                        
                        print(f"Attempting download: {text} -> {href}")
                        with page.expect_download(timeout=10000) as download_info:
                            link.click()
                        download = download_info.value
                        download.save_as(save_path)
                        print(f"--- HARVEST SUCCESS: {filename} ({os.path.getsize(save_path)} bytes) ---")
                    except Exception as e:
                        print(f"Download skip ({text}): {str(e)[:50]}")

            browser.close()

    def harvest_tvpl(self):
        print("Starting Aggressive TVPL Harvest...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            
            # Login
            page.goto("https://thuvienphapluat.vn/page/login.aspx")
            page.fill("#UserName", self.user)
            page.fill("#Password", self.password)
            page.click("#Button1")
            page.wait_for_load_state("networkidle")
            print("TVPL Login Successful.")
            
            # Direct target: Education Law 2019 (often code 367552)
            search_query = "Quy định đào tạo đại học năm 2021"
            page.goto(f"https://thuvienphapluat.vn/tim-kiem-van-ban.aspx?keyword={search_query}")
            page.wait_for_timeout(5000)
            
            # Find download buttons
            dl_links = page.locator("a[href*='DownLoad.aspx']").all()
            for i, link in enumerate(dl_links[:3]):
                try:
                    save_path = os.path.join(self.download_dir, f"TVPL_Law_{i}.pdf")
                    with page.expect_download() as download_info:
                        link.click()
                    download = download_info.value
                    download.save_as(save_path)
                    print(f"--- TVPL HARVEST SUCCESS: TVPL_Law_{i}.pdf ({os.path.getsize(save_path)} bytes) ---")
                except Exception as e:
                    print(f"TVPL skip: {e}")
            
            browser.close()

if __name__ == "__main__":
    harvester = MasterHarvester()
    harvester.harvest_hctlu()
    harvester.harvest_tvpl()
