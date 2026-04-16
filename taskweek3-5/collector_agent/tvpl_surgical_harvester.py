import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

def tvpl_harvest():
    user = os.getenv("THU_VIEN_PHAP_LUAT_USER", "dxdung")
    password = os.getenv("THU_VIEN_PHAP_LUAT_PASS", "Dolinhdan2014")
    download_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw"
    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("TVPL Infiltration: Logging in...")
        page.goto("https://thuvienphapluat.vn/page/login.aspx")
        page.fill("#UserName", user)
        page.fill("#Password", password)
        page.click("#Button1")
        page.wait_for_load_state("networkidle")
        
        # Search specifically for Training Regulations
        queries = [
            "Quy định đào tạo đại học theo tín chỉ 2021 Thủy lợi",
            "Luật Giáo dục đại học 2018",
            "Luật Viên chức"
        ]
        
        for query in queries:
            print(f"Searching TVPL: {query}")
            page.goto(f"https://thuvienphapluat.vn/tim-kiem-van-ban.aspx?keyword={query}")
            page.wait_for_timeout(5000)
            
            # Find the first result and click it
            links = page.locator(".content-timkiem a[href*='id=']").all()
            if len(links) > 0:
                links[0].click()
                page.wait_for_timeout(5000)
                
                # Look for 'Tải văn bản' or download icons
                # TVPL often uses a dynamic download popup
                try:
                    dl_trigger = page.locator("a:has-text('Tải về'), a[title*='Tải văn bản']")
                    if dl_trigger.count() > 0:
                        with page.expect_download(timeout=60000) as download_info:
                            dl_btn = dl_trigger.first
                            dl_btn.click()
                        download = download_info.value
                        filename = f"TVPL_{query.replace(' ', '_')}.pdf"
                        download.save_as(os.path.join(download_dir, filename))
                        print(f"+++ TVPL HARVESTED: {filename} ({os.path.getsize(os.path.join(download_dir, filename))} bytes)")
                except Exception as e:
                    print(f"Failed TVPL download for {query}: {e}")

        browser.close()

if __name__ == "__main__":
    tvpl_harvest()
