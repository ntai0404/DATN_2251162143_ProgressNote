import sys
import os
import time

# Add required paths
sys.path.append(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\collector-agent")
from web_scraper import WebScraper

def prove():
    print(f"--- LIVE SYSTEM AUDIT: {time.ctime()} ---")
    print(f"Working Directory: {os.getcwd()}")
    
    scraper = WebScraper()
    print("Initiating live scrape of TLU News...")
    results = scraper.scrape_tlu_news()
    
    if results:
        print(f"SUCCESS: Scraped {len(results)} items live.")
        print("Top 3 current news items:")
        for res in results[:3]:
            print(f"- {res['title']} ({res['url']})")
    else:
        print("FAILED: No items found. Check internet connection.")

if __name__ == "__main__":
    prove()
