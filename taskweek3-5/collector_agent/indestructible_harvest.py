import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

def indestructible_harvest():
    user = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
    password = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")
    download_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw"
    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 1024})
        page = context.new_page()
        
        print("Indestructible Harvester: Logging in...")
        try:
            page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74", timeout=60000)
            page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", user)
            page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", password)
            page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
            page.wait_for_load_state("networkidle")
            
            print("Navigating to Document Module...")
            # Direct navigation if possible or click sequence
            page.click("text=Quản lý văn bản")
            page.wait_for_timeout(3000)
            page.click("text=Văn bản quản lý")
            page.wait_for_timeout(5000)
            
            # Find all download links
            # The portal uses a table with 'Download' links
            rows = page.locator("tr").all()
            print(f"Discovered {len(rows)} potential regulatory entries.")
            
            for i in range(len(rows)):
                try:
                    row = rows[i]
                    text = row.inner_text()
                    if "Download" in text:
                        cells = row.locator("td").all()
                        if len(cells) > 1:
                            title = cells[1].inner_text().strip()
                            safe_filename = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).strip()[:100] + ".pdf"
                            full_path = os.path.join(download_dir, safe_filename)
                            
                            if os.path.exists(full_path):
                                print(f"Skip (Exists): {safe_filename}")
                                continue
                                
                            print(f"Targeting [{i}]: {title}")
                            dl_btn = row.locator("a").filter(has_text="Download")
                            if dl_btn.count() > 0:
                                with page.expect_download(timeout=120000) as download_info:
                                    dl_btn.first.click()
                                download = download_info.value
                                download.save_as(full_path)
                                print(f"+++ HARVESTED: {safe_filename} ({os.path.getsize(full_path)} bytes)")
                                # Wait a bit between downloads to avoid server throttle
                                time.sleep(2)
                except Exception as e:
                    print(f"Error harvesting row {i}: {e}")
                    
        except Exception as big_e:
            print(f"Indestructible Harvester CRASHED: {big_e}")
        finally:
            browser.close()

if __name__ == "__main__":
    indestructible_harvest()
