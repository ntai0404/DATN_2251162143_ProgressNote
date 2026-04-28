import os
import time
import random
import logging
import sys
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Set encoding for Windows console
if sys.platform == "win32":
    import _locale
    _locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])
    sys.stdout.reconfigure(encoding='utf-8')

# --- Configuration ---
SCRATCH_DIR = Path(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\scratch\TVPL-test-get")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"
TEST_URL = "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-367665.aspx"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("TVPL-Smart-Harvester")

def clean_and_join_text(text):
    """
    Intelligently joins lines that were split by HTML layout but belong to the same sentence.
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    current_paragraph = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_paragraph:
                cleaned_lines.append(current_paragraph)
                current_paragraph = ""
            continue
            
        # If it looks like a Header (Điều, Chương, Mục), flush current paragraph and add as separate line
        if re.match(r'^(Điều|Chương|Phần|Mục|Phụ lục|Khoản|Điểm)\s+\d+|^\d+\.', line, re.IGNORECASE):
            if current_paragraph:
                cleaned_lines.append(current_paragraph)
                current_paragraph = ""
            cleaned_lines.append(line)
            continue
            
        if not current_paragraph:
            current_paragraph = line
        else:
            # Check if we should join
            # Rule: If current_paragraph ends with lowercase, comma, or no punctuation, join.
            # Vietnamese specific: lowercase letters with accents are handled by \w
            last_char = current_paragraph[-1]
            if last_char in ',;-' or last_char.islower() or (last_char.isalpha() and last_char.islower()):
                current_paragraph += " " + line
            elif last_char in '.!?:' or last_char.isdigit():
                # Ends with sentence terminator or digit (likely end of a list item)
                cleaned_lines.append(current_paragraph)
                current_paragraph = line
            else:
                # Default: join with a space to be safe
                current_paragraph += " " + line
                
    if current_paragraph:
        cleaned_lines.append(current_paragraph)
        
    return '\n\n'.join(cleaned_lines)

def scrape_direct_text(url):
    with sync_playwright() as p:
        log.info("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # 1. Login
        log.info("Logging into TVPL...")
        page.goto("https://thuvienphapluat.vn/page/login.aspx")
        page.fill("#UserName", TVPL_USER)
        page.fill("#Password", TVPL_PASS)
        page.click("#Button1")
        page.wait_for_timeout(3000)

        # 2. Navigate to Target
        log.info(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")
        time.sleep(5)

        # 3. Extraction
        log.info("Applying Smart 'Bôi đen & Lọc' logic...")
        
        result = page.evaluate("""
            () => {
                const container = document.querySelector('#divContentDoc') || 
                                  document.querySelector('.content1');
                
                if (!container) return { error: "Content container not found" };
                
                const title = document.querySelector('h1')?.innerText.trim() || "Untitled";
                
                // Minimal DOM cleaning
                const noise = container.querySelectorAll('.noprint, script, style, .ads');
                noise.forEach(n => n.remove());

                return {
                    title: title,
                    raw_text: container.innerText
                };
            }
        """)

        if "error" in result:
            log.error(result["error"])
            return

        # 4. Smart Post-processing in Python (easier to debug regex)
        log.info("Cleaning and joining fragmented lines...")
        final_content = clean_and_join_text(result['raw_text'])

        # 5. Save result
        filename = "Luat_Giao_duc_2019_SMART_Extracted.md"
        output_path = SCRATCH_DIR / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {result['title']}\n\n")
            f.write(final_content)
        
        log.info(f"✅ Success! Extracted {len(final_content)} characters.")
        log.info(f"File saved to: {output_path}")
        browser.close()

if __name__ == "__main__":
    scrape_direct_text(TEST_URL)
