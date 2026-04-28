import os
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("TVPLService")

class TVPLService:
    def __init__(self, cookies_str: str = None):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        if cookies_str:
            self.set_cookies(cookies_str)

    def set_cookies(self, cookies_str: str):
        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                self.session.cookies.set(k, v, domain=".thuvienphapluat.vn")

    def fetch_document(self, url: str, output_path: Path) -> bool:
        """
        Navigates to the TVPL page, finds the download ID, and downloads the .doc file.
        Returns True if a REAL document was downloaded, False otherwise.
        """
        log.info(f"Targeting: {url}")
        try:
            self.headers["Referer"] = url
            resp = self.session.get(url, headers=self.headers, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Check for Captcha
            if soup.title and "Captcha" in soup.title.string:
                log.error("CAPTCHA detected. Access blocked.")
                return False

            # Discovery logic (Selector + Regex fallback)
            doc_id = self._discover_doc_id(soup, resp.text)
            
            if not doc_id:
                log.error(f"Could not find Download ID on {url}")
                return False

            log.info(f"Found Download ID: {doc_id}")
            dl_url = f"https://thuvienphapluat.vn/documents/download.aspx?id={doc_id}&part=-1"
            
            # Download attempt
            dl_resp = self.session.get(dl_url, headers=self.headers, timeout=60)
            
            if dl_resp.status_code == 200:
                content = dl_resp.content
                # Basic check for REAL OLE2 header (D0 CF 11 E0)
                if content.startswith(b'\xd0\xcf\x11\xe0'):
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(content)
                    log.info(f"Successfully downloaded: {output_path.name} ({len(content)} bytes)")
                    return True
                else:
                    log.error(f"Downloaded file for {url} is not a valid Word doc (might be error page).")
                    return False
            else:
                log.error(f"Download failed with status {dl_resp.status_code}")
                return False

        except Exception as e:
            log.error(f"Error fetching {url}: {e}")
            return False

    def _discover_doc_id(self, soup, html_text) -> str:
        # 1. Try standard selector
        link = soup.find("a", {"id": "ctl00_Content_ThongTinVB_vietnameseHyperLink"})
        if not link:
            link = soup.find("a", href=lambda x: x and "download.aspx" in x and "id=" in x)
        
        if link and link.get("href"):
            match = re.search(r"id=([^&]+)", link["href"])
            if match:
                return match.group(1)
        
        # 2. Regex fallback
        patterns = [
            r"id=([a-zA-Z0-9%]{20,})", 
            r"download\.aspx\?id=([^&\"']+)",
            r"vietnameseHyperLink.*?id=([^&\"']+)"
        ]
        for p in patterns:
            matches = re.findall(p, html_text)
            if matches:
                return matches[0]
        
        return None
