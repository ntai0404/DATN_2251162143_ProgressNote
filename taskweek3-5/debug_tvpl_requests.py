"""
TVPL HTTP Session Scraper (requests-based)
- Uses requests.Session to handle cookies properly
- Handles ASP.NET ViewState login form
- Searches and extracts .nqTitle links
"""
import requests
from bs4 import BeautifulSoup
import re, time, sys
from pathlib import Path

TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"
BASE = "https://thuvienphapluat.vn"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def login_tvpl():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Get login page (fetch ViewState)
    r = session.get(f"{BASE}/page/login.aspx", timeout=20)
    soup = BeautifulSoup(r.content, "html.parser")
    
    viewstate = soup.find("input", {"id": "__VIEWSTATE"})
    eventval  = soup.find("input", {"id": "__EVENTVALIDATION"})
    viewstategenerator = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
    
    data = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate["value"] if viewstate else "",
        "__EVENTVALIDATION": eventval["value"] if eventval else "",
        "__VIEWSTATEGENERATOR": viewstategenerator["value"] if viewstategenerator else "",
        "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolder1$UserName": TVPL_USER,
        "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolder1$Password": TVPL_PASS,
        "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolder1$Button1": "Đăng nhập",
    }
    
    r2 = session.post(f"{BASE}/page/login.aspx", data=data, timeout=20, allow_redirects=True)
    
    print(f"Login status: {r2.status_code} -> {r2.url}")
    logged_in = "login" not in r2.url.lower()
    print(f"Logged in: {logged_in}")
    
    # Handle dll=true (duplicate login) - accept and continue
    if "dll=true" in r2.url:
        soup2 = BeautifulSoup(r2.content, "html.parser")
        agree_btn = soup2.find("input", {"value": re.compile(r"ng ý|Dong y", re.I)})
        if agree_btn:
            form = soup2.find("form")
            if form:
                action = form.get("action", "/page/login.aspx")
                # Re-submit with agree
                vs2 = soup2.find("input", {"id": "__VIEWSTATE"})
                ev2 = soup2.find("input", {"id": "__EVENTVALIDATION"})
                data2 = {
                    "__VIEWSTATE": vs2["value"] if vs2 else "",
                    "__EVENTVALIDATION": ev2["value"] if ev2 else "",
                    agree_btn.get("name", "btnDongY"): agree_btn.get("value", "Dong y"),
                }
                r3 = session.post(f"{BASE}{action}", data=data2, timeout=20, allow_redirects=True)
                print(f"After agree: {r3.url}")
    
    return session

def search_tvpl(session, keyword, max_pages=2):
    results = []
    encoded = requests.utils.quote(keyword)
    
    for pg in range(1, max_pages + 1):
        url = f"{BASE}/tim-van-ban.aspx?keyword={encoded}&area=1&page={pg}"
        print(f"Searching: {url}")
        r = session.get(url, timeout=20)
        soup = BeautifulSoup(r.content, "html.parser")
        
        items = soup.select(".nqTitle a")
        if not items:
            items = soup.select("p.nqTitle a")
        if not items:
            items = soup.select("a[href*='/van-ban/']")
        
        print(f"  Page {pg}: {len(items)} items found")
        
        for item in items:
            href = item.get("href", "")
            title = item.get_text(strip=True)
            if href and "/van-ban/" in href and title:
                full_url = href if href.startswith("http") else BASE + href
                results.append((title, full_url))
        
        if not items:
            break
        time.sleep(1)
    
    return results

def scrape_noidung(session, url):
    """Scrape from 'Noi dung' tab."""
    r = session.get(url, timeout=20)
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Try main content selectors
    content = None
    for sel in [".content1", "#divContent", ".vbContent", ".noidung-vb"]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 300:
            content = el.get_text(separator="\n", strip=True)
            print(f"  Text via '{sel}': {len(content)} chars")
            break
    
    return content or ""

if __name__ == "__main__":
    session = login_tvpl()
    results = search_tvpl(session, "thong tu 08 2021 dao tao dai hoc", max_pages=2)
    print(f"\nTotal found: {len(results)}")
    for title, url in results[:5]:
        print(f"  - {title[:60]}")
    
    # Test scraping first result
    if results:
        title, url = results[0]
        print(f"\nScraping: {url}")
        text = scrape_noidung(session, url)
        print(f"Content length: {len(text)}")
        print(f"Preview: {text[:300]}")
