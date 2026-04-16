import sys
import os
import time

# Add required paths
sys.path.append(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\collector-agent")
from playwright.sync_api import sync_playwright

def download_via_browser():
    print(f"--- BROWSER-BASED ACQUISITION: {time.ctime()} ---")
    download_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_downloads"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        # Navigate to a real page with a document
        url = "https://tlu.edu.vn/tin-tuc-thong-bao/thong-bao/thong-bao-dao-tao/thong-bao-v-v-dang-ky-va-nop-le-phi-hoc-lai-va-thi-lai-hoc-ky-2-nam-hoc-2023-2024-15243/"
        print(f"Navigating to TLU Notification: {url}")
        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # Take a screenshot as visual evidence
        screenshot_path = os.path.join(download_dir, "portal_evidence.png")
        page.screenshot(path=screenshot_path)
        print(f"Captured visual evidence at {screenshot_path}")
        
        # Look for the 'view document' or link
        links = page.locator("a").all()
        for link in links:
            href = link.get_attribute("href")
            if href and (".pdf" in href.lower() or "drive.google" in href):
                print(f"FOUND DOCUMENT LINK: {href}")
                # For drive links, we just report it
                with open(os.path.join(download_dir, "found_links.txt"), "a") as f:
                    f.write(f"{href}\n")
        
        browser.close()
    print("Investigation Complete.")

if __name__ == "__main__":
    download_via_browser()
