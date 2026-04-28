import os
import time
import random
import logging
import sys
import re
import json
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
STATE_FILE = SCRATCH_DIR / "spider_state.json"
DATA_DIR = SCRATCH_DIR / "data_extracted"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"

RELEVANT_KEYWORDS = [
    "giao-duc", "dao-tao", "sinh-vien", "hoc-sinh", "nha-giao",
    "hoc-bong", "tuyen-sinh", "cong-chuc", "vien-chuc", "quy-che"
]

INITIAL_SEEDS = [
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-367665.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-Giao-duc-dai-hoc-2012-142762.aspx",
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-10-2016-TT-BGDDT-quy-che-cong-tac-sinh-vien-chuong-trinh-dao-tao-dai-hoc-he-chinh-quy-308413.aspx"
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(SCRATCH_DIR / "spider.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("TVPL-Spider-V3")

class TVPLSpider:
    def __init__(self, max_docs=15):
        self.max_docs = max_docs
        self.state = self.load_state()

    def load_state(self):
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"queue": INITIAL_SEEDS[:], "processed": [], "count": 0}

    def save_state(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def normalize_url(self, url):
        return url.split('?')[0].split('#')[0].strip()

    def clean_and_join_text(self, text):
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
            if re.match(r'^(Điều|Chương|Phần|Mục|Phụ lục|Khoản|Điểm)\s+\d+|^\d+\.', line, re.IGNORECASE):
                if current_paragraph:
                    cleaned_lines.append(current_paragraph)
                    current_paragraph = ""
                cleaned_lines.append(line)
                continue
            if not current_paragraph:
                current_paragraph = line
            else:
                last_char = current_paragraph[-1]
                if last_char in ',;-' or last_char.islower():
                    current_paragraph += " " + line
                elif last_char in '.!?:' or last_char.isdigit():
                    cleaned_lines.append(current_paragraph)
                    current_paragraph = line
                else:
                    current_paragraph += " " + line
        if current_paragraph:
            cleaned_lines.append(current_paragraph)
        return '\n\n'.join(cleaned_lines)

    def is_relevant(self, url):
        return any(k in url.lower() for k in RELEVANT_KEYWORDS)

    def run(self):
        with sync_playwright() as p:
            log.info("Starting TVPL Spider V3 (with Legal Metadata)...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            log.info("Logging into TVPL...")
            page.goto("https://thuvienphapluat.vn/page/login.aspx")
            page.fill("#UserName", TVPL_USER)
            page.fill("#Password", TVPL_PASS)
            page.click("#Button1")
            page.wait_for_timeout(3000)

            while self.state["queue"] and self.state["count"] < self.max_docs:
                url = self.normalize_url(self.state["queue"].pop(0))
                if url in self.state["processed"]:
                    continue

                log.info(f"[{self.state['count']+1}/{self.max_docs}] Harvesting: {url}")
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    time.sleep(3)

                    extraction = page.evaluate("""
                        () => {
                            const container = document.querySelector('#divContentDoc') ||
                                              document.querySelector('.content1');
                            if (!container) return null;

                            const title = document.querySelector('h1')?.innerText.trim() || "";

                            // --- Legal Metadata Extraction ---
                            const meta = { status: '', issued_date: '', effective_date: '' };

                            // Try common status badge selectors on TVPL
                            const statusEl = document.querySelector('.label-status, .status-doc span, .hieu-luc');
                            if (statusEl) meta.status = statusEl.innerText.trim();

                            // Scan all text nodes in info tables for key fields
                            document.querySelectorAll('table tr, .vb-thuoc-tinh li, .vbThuocTinh li').forEach(row => {
                                const t = row.innerText || '';
                                if (!meta.status && (t.includes('Còn hiệu lực') || t.includes('Hết hiệu lực') || t.includes('Chưa có hiệu lực'))) {
                                    if (t.includes('Còn hiệu lực')) meta.status = 'Còn hiệu lực';
                                    else if (t.includes('Hết hiệu lực')) meta.status = 'Hết hiệu lực';
                                    else meta.status = 'Chưa có hiệu lực';
                                }
                                if (t.includes('Ngày ban hành') || t.includes('Ban hành')) {
                                    const m = t.match(/\d{2}\/\d{2}\/\d{4}/);
                                    if (m && !meta.issued_date) meta.issued_date = m[0];
                                }
                                if (t.includes('Ngày hiệu lực') || t.includes('Hiệu lực từ')) {
                                    const m = t.match(/\d{2}\/\d{2}\/\d{4}/);
                                    if (m && !meta.effective_date) meta.effective_date = m[0];
                                }
                            });

                            // Relationship detection (replaced_by / replaces)
                            const replaced_by = [];
                            const replaces = [];
                            document.querySelectorAll('a[href*="/van-ban/"]').forEach(a => {
                                const ctx = a.closest('li, tr, p')?.innerText || '';
                                if (ctx.match(/thay thế|bị bãi bỏ|bị thay/i))
                                    replaced_by.push(a.innerText.trim());
                                else if (ctx.match(/thay thế cho|bãi bỏ văn bản/i))
                                    replaces.push(a.innerText.trim());
                            });

                            // Discover outbound links for queue
                            const links = Array.from(document.querySelectorAll('a[href*="/van-ban/"]'))
                                .map(a => a.href)
                                .filter(h => h.startsWith('https://thuvienphapluat.vn/van-ban/'));

                            // Clean noise from content container
                            container.querySelectorAll('.noprint, script, style, .ads').forEach(n => n.remove());

                            return {
                                title,
                                raw_text: container.innerText,
                                discovered_links: links,
                                meta,
                                replaced_by,
                                replaces
                            };
                        }
                    """)

                    # Validation
                    if not extraction or not extraction['title']:
                        log.warning(f"⚠️ Skip (no title): {url}")
                        self.state["processed"].append(url)
                        continue

                    content = self.clean_and_join_text(extraction['raw_text'])
                    if len(content) < 500:
                        log.warning(f"⚠️ Skip (too short): {url}")
                        self.state["processed"].append(url)
                        continue

                    # Build YAML frontmatter — this is what the RAG Collector reads
                    meta = extraction.get('meta', {})
                    status = meta.get('status', 'Không rõ') or 'Không rõ'
                    frontmatter = (
                        "---\n"
                        f'title: "{extraction["title"]}"\n'
                        f'status: "{status}"\n'
                        f'issued_date: "{meta.get("issued_date", "")}"\n'
                        f'effective_date: "{meta.get("effective_date", "")}"\n'
                        f'replaced_by: "{"; ".join(extraction.get("replaced_by", []))}"\n'
                        f'replaces: "{"; ".join(extraction.get("replaces", []))}"\n'
                        f'source: "{url}"\n'
                        "---\n"
                    )

                    safe_name = "".join([c if c.isalnum() else "_" for c in extraction['title'][:100]])
                    file_path = DATA_DIR / f"{safe_name}.md"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(frontmatter)
                        f.write(f"\n# {extraction['title']}\n\n")
                        f.write(content)

                    # Enqueue discovered links (normalized, deduped, relevant)
                    for link in extraction['discovered_links']:
                        norm = self.normalize_url(link)
                        if norm not in self.state["processed"] and norm not in self.state["queue"]:
                            if self.is_relevant(norm):
                                self.state["queue"].append(norm)

                    self.state["processed"].append(url)
                    self.state["count"] += 1
                    log.info(f"✅ [{status}] Saved: {file_path.name}")

                except Exception as e:
                    log.error(f"Error on {url}: {e}")
                    self.state["processed"].append(url)

                self.save_state()
                time.sleep(random.uniform(3, 7))

            log.info(f"Spider V3 done. Total harvested: {self.state['count']}")
            browser.close()

if __name__ == "__main__":
    spider = TVPLSpider(max_docs=15)
    spider.run()
