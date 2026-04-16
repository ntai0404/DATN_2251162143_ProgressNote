import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

def surgical_harvest():
    user = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
    password = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")
    download_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw"
    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headless=False to see what we're doing
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("Surgical Infiltration: Logging in...")
        page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74")
        page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", user)
        page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", password)
        page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
        page.wait_for_load_state("networkidle")
        
        # Navigate to Documents
        print("Navigating to Document Module...")
        page.click("text=Quản lý văn bản")
        page.wait_for_timeout(2000)
        page.click("text=Văn bản quản lý")
        page.wait_for_timeout(5000)
        
        # Get all rows
        rows = page.locator("tr").all()
        print(f"Discovered {len(rows)} regulatory entries.")
        
        # Harvest specific targets
        for i in range(len(rows)):
            try:
                row = rows[i]
                text = row.inner_text()
                if "Download" in text:
                    title_cells = row.locator("td").all()
                    if len(title_cells) > 1:
                        title = title_cells[1].inner_text().strip()
                        print(f"Targeting Item {i}: {title}")
                        
                        dl_btn = row.locator("a").filter(has_text="Download")
                        if dl_btn.count() > 0:
                            # Use first match if multiple
                            with page.expect_download(timeout=60000) as download_info:
                                dl_btn.first.click()
                            download = download_info.value
                            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).strip()[:80]
                            filename = f"{safe_title}.pdf"
                            download.save_as(os.path.join(download_dir, filename))
                            print(f"+++ HARVESTED: {filename} ({os.path.getsize(os.path.join(download_dir, filename))} bytes)")
            except Exception as e:
                print(f"Failed to harvest row {i}: {e}")
        
        browser.close()

if __name__ == "__main__":
    surgical_harvest()
