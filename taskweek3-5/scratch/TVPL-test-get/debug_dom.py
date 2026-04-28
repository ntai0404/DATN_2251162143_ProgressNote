import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

SCRATCH_DIR = Path(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\scratch\TVPL-test-get")
TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"
TEST_URL = "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-367665.aspx"

def debug_dom(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        print("Logging in...")
        page.goto("https://thuvienphapluat.vn/page/login.aspx")
        page.fill("#UserName", TVPL_USER)
        page.fill("#Password", TVPL_PASS)
        page.click("#Button1")
        page.wait_for_timeout(3000)

        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")
        time.sleep(5)
        
        # Take a screenshot for visual debugging
        page.screenshot(path=str(SCRATCH_DIR / "debug_page.png"))
        print(f"Screenshot saved to {SCRATCH_DIR / 'debug_page.png'}")

        # Find potential content containers
        analysis = page.evaluate("""
            () => {
                const results = [];
                // Find all divs with 'content' in their ID or Class
                const divs = Array.from(document.querySelectorAll('div'));
                divs.forEach(d => {
                    const id = d.id || "";
                    const cls = d.className || "";
                    if (id.toLowerCase().includes('content') || cls.toLowerCase().includes('content')) {
                        results.push({ id, class: cls, textLen: d.innerText.length });
                    }
                });
                
                // Sort by text length to find the main content
                results.sort((a, b) => b.textLen - a.textLen);
                return results.slice(0, 10);
            }
        """)
        
        print("Potential containers found:")
        for r in analysis:
            print(f"ID: {r['id']}, Class: {r['class']}, Text Length: {r['textLen']}")
        
        # Try to find the one that has "Luật Giáo dục" in it
        best_guess = page.evaluate("""
            () => {
                const all = Array.from(document.querySelectorAll('div'));
                const candidates = all.filter(d => d.innerText.includes("Luật Giáo dục") && d.innerText.length > 5000);
                return candidates.map(d => ({ id: d.id, class: d.className, textLen: d.innerText.length }));
            }
        """)
        print("\nBest candidates (matching 'Luật Giáo dục'):")
        for c in best_guess:
            print(f"ID: {c['id']}, Class: {c['class']}, Text Length: {c['textLen']}")

        browser.close()

if __name__ == "__main__":
    debug_dom(TEST_URL)
