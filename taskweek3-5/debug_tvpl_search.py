from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    
    # Login
    page.goto("https://thuvienphapluat.vn/page/login.aspx", timeout=60000, wait_until="domcontentloaded")
    page.fill("#UserName", "P2")
    page.fill("#Password", "dhtl123456")
    page.click("#Button1")
    page.wait_for_timeout(4000)
    
    # Handle overlap popup using JS
    page.evaluate("Array.from(document.querySelectorAll('input,button')).find(el => (el.value||el.innerText||'').includes('ng'+'y') || (el.value||el.innerText||'').includes('ng \u00fd'))?.click()")
    page.wait_for_timeout(2000)
    
    print("URL after login:", page.url)
    print("Logged in?", "login" not in page.url.lower())

    # Search
    page.goto("https://thuvienphapluat.vn/tim-van-ban.aspx?keyword=thong+tu+08+2021&area=1", timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    selectors_to_try = [".nqTitle a", "p.nqTitle a", "a[href*='/van-ban/']", "h4 a", ".ten-vb a"]
    for sel in selectors_to_try:
        items = page.query_selector_all(sel)
        if items:
            print(f"[OK] Selector '{sel}': {len(items)} items")
            for item in items[:2]:
                print(f"    - {item.inner_text()[:60]}")
            break
        else:
            print(f"[--] Selector '{sel}': 0 items")

    browser.close()
