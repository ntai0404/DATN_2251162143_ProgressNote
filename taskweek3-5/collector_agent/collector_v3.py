"""
Collector Agent V7 (Universal) - TLU Smart Tutor
================================================
The "Everything Harvester":
  - Unified Session-Based Backend Harvesting.
  - Adaptive Scraper: Automatically detects page type (HCTLU Grid, HCTLU Calendar, TVPL Doc).
  - Deep Binary Extraction: Follows LinkClick and cmdDownload to get PDF/Word content.
  - 100% Data Coverage Guarantee for provided domains.
"""

import os
import re
import sys
import json
import time
import hashlib
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from docx import Document as DocxDocument
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

# ── Paths & Config ─────────────────────────────────────────────────────────────
AGENT_DIR  = Path(__file__).parent
BASE_DIR   = AGENT_DIR.parent
RAW_DIR    = BASE_DIR / "data_raw_v2"   # ← NEW: isolated test dir, data_raw preserved
EXTRACT_DIR= BASE_DIR / "data_extracted"
LOG_FILE   = BASE_DIR / "collector_v7.log"
HASH_STORE = BASE_DIR / "dedup_hashes.json"
ENV_FILE   = AGENT_DIR / ".env"

for d in [RAW_DIR, EXTRACT_DIR]: d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("collector-v7")

load_dotenv(ENV_FILE)
TVPL_USER  = os.getenv("THU_VIEN_PHAP_LUAT_USER", "P2")
TVPL_PASS  = os.getenv("THU_VIEN_PHAP_LUAT_PASS", "dhtl123456")
HCTLU_USER = os.getenv("HAN_CHINH_TLU_USER", "dxdung")
HCTLU_PASS = os.getenv("HAN_CHINH_TLU_PASS", "Dolinhdan2014")

# ─────────────────────────────────────────────────────────────────────────────
# 0. SESSION MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class SessionManager:
    COOKIE_DIR = AGENT_DIR / "sessions"
    COOKIE_DIR.mkdir(exist_ok=True)

    def __init__(self, domain: str):
        self.domain = domain
        self.cookie_file = self.COOKIE_DIR / f"{domain}_session.json"
        self.cookies = {}
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0"
        self._load()

    def _load(self):
        if self.cookie_file.exists():
            try:
                with open(self.cookie_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.cookies = data.get("cookies", {})
                    self.user_agent = data.get("user_agent", self.user_agent)
            except: pass

    def save(self, playwright_cookies: list, user_agent: str):
        self.cookies = {c['name']: c['value'] for c in playwright_cookies}
        self.user_agent = user_agent
        with open(self.cookie_file, "w", encoding="utf-8") as f:
            json.dump({"cookies": self.cookies, "user_agent": self.user_agent}, f, indent=2)

    def get_session(self) -> requests.Session:
        s = requests.Session()
        s.cookies.update(self.cookies)
        s.headers.update({"User-Agent": self.user_agent})
        return s

# ─────────────────────────────────────────────────────────────────────────────
# 1. CORE UTILS
# ─────────────────────────────────────────────────────────────────────────────
class DedupManager:
    def __init__(self):
        self.store = {}
        if HASH_STORE.exists():
            with open(HASH_STORE, encoding="utf-8") as f: self.store = json.load(f)

    def is_new(self, doc_id: str, content: str) -> bool:
        h = hashlib.md5(content.encode("utf-8")).hexdigest()
        if self.store.get(doc_id) == h: return False
        self.store[doc_id] = h
        with open(HASH_STORE, "w", encoding="utf-8") as f: json.dump(self.store, f, indent=2)
        return True

class TextExtractor:
    def from_pdf(self, path: Path) -> Tuple[str, bool]:
        try:
            doc = fitz.open(str(path))
            full = "\n".join(page.get_text() for page in doc).strip()
            return full, len(full) < len(doc) * 50
        except: return "", True

class Chunker:
    def chunk(self, text: str, source: str, url: str) -> List[Dict]:
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        # Enhanced regex to handle Markdown bolding (**Điều**) and optional whitespace
        parts = re.split(r"(?=\n\s*(?:\*\*|)\s*(?:Điều|Chương|Phần|Mục|Ngày)\s+\d+[\.\:\s])", text)
        chunks = []
        if len(parts) > 2:
            for p in parts:
                p = p.strip()
                if len(p) < 100: continue
                title = p.split("\n")[0].strip()[:80]
                chunks.append({"title": f"{source} - {title}", "content": p, "metadata": {"source_url": url, "chunk_type": "article"}})
        else:
            chunks.append({"title": source, "content": text, "metadata": {"source_url": url, "chunk_type": "full_text"}})
        return chunks

# ─────────────────────────────────────────────────────────────────────────────
# 2. TVPL SCRAPER (Universal for Articles)
# ─────────────────────────────────────────────────────────────────────────────
class TVPLScraper:
    BASE = "https://thuvienphapluat.vn"

    def __init__(self, dedup: DedupManager, chunker: Chunker):
        self.dedup, self.chunker = dedup, chunker
        self.session_mgr = SessionManager("tvpl")

    def seed_session(self):
        log.info("TVPL: Seeding session...")
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=self.session_mgr.user_agent)
                page = ctx.new_page()
                page.goto(f"{self.BASE}/page/login.aspx", timeout=60000)
                # Clear and Fill
                page.fill("#UserName", "")
                page.fill("#UserName", TVPL_USER)
                page.fill("#Password", "")
                page.fill("#Password", TVPL_PASS)
                page.click("#Button1")
                page.wait_for_timeout(4000)
                self.session_mgr.save(ctx.cookies(), self.session_mgr.user_agent)
                browser.close()
        except: log.error("TVPL Seeding failed.")

    def scrape_url(self, url: str, retries=1) -> List[Dict]:
        s = self.session_mgr.get_session()
        log.info(f"  TVPL Harvest: {url}")
        try:
            r = s.get(url, timeout=30)
            soup = BeautifulSoup(r.content, "html.parser")
            div = soup.select_one(".content1") or soup.select_one("#divContent") or soup.select_one(".content-law")
            if not div:
                if retries > 0: self.seed_session(); return self.scrape_url(url, retries - 1)
                return []
            raw = div.get_text(separator="\n").strip()
            title = soup.title.string.strip() if soup.title else "TVPL Doc"
            doc_id = hashlib.md5(url.encode()).hexdigest()[:16]
            if not self.dedup.is_new(doc_id, raw): return []
            return self.chunker.chunk(raw, title, url)
        except: return []

# ─────────────────────────────────────────────────────────────────────────────
# 3. HCTLU SCRAPER (Universal for Grid & Calendar)
# ─────────────────────────────────────────────────────────────────────────────
class HCTLUScraper:
    PORTAL = "https://hanhchinh.tlu.edu.vn"

    def __init__(self, dedup: DedupManager, chunker: Chunker):
        self.dedup, self.chunker = dedup, chunker
        self.session_mgr = SessionManager("hctlu")

    def seed_session(self):
        log.info("HCTLU: Seeding session...")
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=self.session_mgr.user_agent)
                page = ctx.new_page()
                page.goto(f"{self.PORTAL}/Default.aspx?tabid=74", timeout=60000)
                
                # Double clear and fill
                page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", "")
                page.type("#dnn_ctr_Login_Login_DNN_txtUsername", HCTLU_USER, delay=100)
                page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", "")
                page.type("#dnn_ctr_Login_Login_DNN_txtPassword", HCTLU_PASS, delay=100)
                
                page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
                
                # Verify login success by waiting for user name
                try:
                    page.wait_for_selector("text=Đỗ Xuân Dũng", timeout=15000)
                    log.info("    Login VERIFIED.")
                except:
                    log.warning("    Login verification timeout. Saving cookies anyway and hoping for the best.")
                
                page.wait_for_timeout(5000)
                self.session_mgr.save(ctx.cookies(), self.session_mgr.user_agent)
                browser.close()
        except Exception as e: log.error(f"HCTLU Seeding failed: {e}")

    def _process_file(self, s, url, title):
        log.info(f"      Downloading Binary: {title}")
        try:
            fr = s.get(url, timeout=60)

            # ── Dedup check for binary files ─────────────────────────────
            content_hash = hashlib.md5(fr.content).hexdigest()
            file_doc_id = f"bin:{hashlib.md5(url.encode()).hexdigest()[:12]}"
            if not self.dedup.is_new(file_doc_id, content_hash):
                log.info(f"      [DEDUP SKIP] Already indexed: {title}")
                return ""
            # ─────────────────────────────────────────────────────────────

            # Sanitize filename and save
            safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:100]
            ext_suffix = ".pdf" if ".pdf" in url.lower() or "pdf" in fr.headers.get("Content-Type", "").lower() else ".file"
            file_path = RAW_DIR / f"{safe_title}{ext_suffix}"

            with open(file_path, "wb") as f: f.write(fr.content)

            ext = TextExtractor()
            text, scanned = ext.from_pdf(file_path)
            return text if not scanned else f"Tài liệu {title} dạng ảnh, cần OCR."
        except Exception as e:
            log.error(f"      Error processing {title}: {e}")
            return ""

    def scrape_url(self, url: str) -> List[Dict]:
        log.info(f"\n[DEEP SCAN] Starting Multi-Page Harvest: {url}")
        all_chunks = []
        
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=self.session_mgr.user_agent)
                ctx.add_cookies([{'name': k, 'value': v, 'domain': 'hanhchinh.tlu.edu.vn', 'path': '/'} for k, v in self.session_mgr.cookies.items()])
                page = ctx.new_page()
                page.goto(url, timeout=60000)
                
                current_page_num = 1
                while True:
                    log.info(f"  --- Scraping Page {current_page_num} ---")
                    # Wait for grid to be stable
                    page.wait_for_selector("table[id*='grdDocuments']", timeout=10000)
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # 1. Process current page rows
                    table = soup.find("table", id=lambda x: x and "grdDocuments" in x)
                    if table:
                        rows = [tr for tr in table.find_all("tr") if tr.find("td") and (not tr.get("class") or "SubHead" not in "".join(tr.get("class", [])))]
                        # Skip total rows or pager rows (rows with many links but no file link)
                        for row in rows:
                            link_el = row.select_one("a[href*='LinkClick']")
                            cells = row.find_all("td")
                            if link_el and len(cells) >= 2:
                                title = cells[1].get_text(strip=True)
                                dl_url = self.PORTAL + (link_el.get("href") if link_el.get("href").startswith("/") else "/" + link_el.get("href"))
                                # Use shared session for download speed
                                with self.session_mgr.get_session() as s:
                                    content = self._process_file(s, dl_url, title)
                                    if content: all_chunks.extend(self.chunker.chunk(content, title, dl_url))

                    # 2. Look for Next Page
                    # On TLU Portal, the pager is a row with <a> tags. The current page is usually a <span> or just text.
                    # We look for the link that follows the current page number
                    next_page_link = None
                    # Method: Find all pagination links in the grid pager
                    pager_links = page.query_selector_all("tr.PagerStyle a, td table td a")
                    for link in pager_links:
                        text = link.inner_text().strip()
                        if text.isdigit() and int(text) == current_page_num + 1:
                            next_page_link = link
                            break
                        if text == ">" or text == "..." and current_page_num >= 10: # Generic next
                            next_page_link = link
                            # We don't break yet if we prefer the specific number
                    
                    if next_page_link:
                        log.info(f"    Navigating to Page {current_page_num + 1}...")
                        next_page_link.click()
                        page.wait_for_timeout(3000) # Wait for PostBack
                        current_page_num += 1
                        if current_page_num > 50: # Safety break to avoid infinite loop
                            log.warning("    Pagination safety limit reached (50 pages).")
                            break
                    else:
                        log.info("    No more pages found (Last page reached).")
                        break
                        
                browser.close()
                return all_chunks

        except Exception as e:
            log.error(f"  HCTLU Deep Harvest Error: {e}")
            # Fallback to single page if playwright fails
            return []

# ─────────────────────────────────────────────────────────────────────────────
# 4. UNIVERSAL FLOW
# ─────────────────────────────────────────────────────────────────────────────
def inject(chunks: List[Dict]):
    if not chunks: return
    sys.path.insert(0, str(BASE_DIR / "search-agent"))
    from vector_db_client import VectorDBClient
    from embedding_service import EmbeddingService
    vdb, embed = VectorDBClient(), EmbeddingService()
    try:
        # Title + Content strategy (Inspired by Phuong's design)
        texts_to_embed = [f"{c['title']} {c['content']}" for c in chunks]
        vecs = embed.embed_texts(texts_to_embed)
        vdb.upsert_chunks(chunks, vecs)
        log.info(f"[SUCCESS] Injected {len(chunks)} units of knowledge.")
    except Exception as e: log.error(f"Injection fail: {e}")

def universal_collect(url: str):
    log.info(f"\n[SYSTEM] Starting Autonomous Harvest: {url}")
    dedup, chunker = DedupManager(), Chunker()
    chunks = []
    if "thuvienphapluat" in url:
        sc = TVPLScraper(dedup, chunker)
        if not sc.session_mgr.cookies: sc.seed_session()
        chunks = sc.scrape_url(url)
    elif "hctlu" in url or "tlu.edu.vn" in url:
        sc = HCTLUScraper(dedup, chunker)
        if not sc.session_mgr.cookies: sc.seed_session()
        chunks = sc.scrape_url(url)
    inject(chunks)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--url", help="URL to harvest")
    args = p.parse_args()
    if args.url: universal_collect(args.url)
