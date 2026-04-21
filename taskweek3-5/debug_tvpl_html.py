import requests
from bs4 import BeautifulSoup

h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
r = requests.get("https://thuvienphapluat.vn/tim-kiem?keyword=thong+tu+08+2021", headers=h)

# Save raw HTML 
with open("tvpl_search_debug.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print("HTML saved to tvpl_search_debug.html")
print("Status:", r.status_code)
print("HTML length:", len(r.text))
print("Has script tags:", r.text.count("<script"))
print("Has van-ban:", r.text.count("/van-ban/"))
