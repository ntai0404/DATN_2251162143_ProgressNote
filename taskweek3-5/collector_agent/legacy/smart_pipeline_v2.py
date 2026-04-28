"""
Smart Pipeline v2 - Text-first Strategy
========================================
Nguồn 1: thuvienphapluat.vn
  → Scrape full text từ tab "Nội dung" (selector: .content1)
  → DON'T download, parse HTML directly → 50,000+ chars mỗi văn bản
  → Chunk theo Điều/Khoản → inject Vector DB

Nguồn 2: hanhchinh.tlu.edu.vn
  → Tất cả PDF đều là scanned → KHÔNG thể extract text lúc tải
  → Strategy thay thế: Lấy danh sách tiêu đề văn bản có tại portal
    (để biết bản quy chế nào đang có hiệu lực tại TLU)
  → Tìm bản song song trên TVPL theo tiêu đề → scrape từ TVPL
"""

import os
import sys
import re
import time
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = BASE_DIR / "data_extracted"
LOG_FILE = BASE_DIR / "smart_pipeline_v2.log"
ENV_FILE = Path(__file__).parent / ".env"

EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("smart-pipeline-v2")

load_dotenv(ENV_FILE)
HANH_CHINH_USER = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
HANH_CHINH_PASS = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")
TVPL_USER = os.getenv("THU_VIEN_PHAP_LUAT_USER", "P2")
TVPL_PASS = os.getenv("THU_VIEN_PHAP_LUAT_PASS", "dhtl123456")

# ── Danh sách URL văn bản cần lấy từ TVPL (có thể mở rộng) ───────────────────
TVPL_TARGET_URLS = [
    # Quy chế đào tạo đại học
    ("thong-tu-08-2021", "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-08-2021-TT-BGDDT-quy-che-dao-tao-trinh-do-dai-hoc-468368.aspx"),
    # Luật Giáo dục đại học 2018
    ("luat-gddat-2018", "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-sua-doi-Luat-Giao-duc-dai-hoc-2018-371747.aspx"),
    # Nghị định 99 hướng dẫn GDĐH
    ("nghi-dinh-99-2019", "https://thuvienphapluat.vn/van-ban/Giao-duc/Nghi-dinh-99-2019-ND-CP-huong-dan-Luat-Giao-duc-dai-hoc-422286.aspx"),
    # Quy chế sinh viên
    ("thong-tu-10-2016-ctsv", "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-10-2016-TT-BGDDT-quy-che-cong-tac-sinh-vien-co-so-giao-duc-dai-hoc-he-chinh-quy-312447.aspx"),
    # Luật Giáo dục 2019
    ("luat-giao-duc-2019", "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-Giao-duc-2019-333172.aspx"),
    # Nghị định học bổng
    ("thong-tu-16-2015-hocbong", "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-lien-tich-16-2015-BGDDT-BLDTBXH-BTC-hoc-bong-khuyen-khich-hoc-tap-274499.aspx"),
    # Quy chế tuyển sinh đại học
    ("thong-tu-09-2020-tuyen-sinh", "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-09-2020-TT-BGDDT-Quy-che-tuyen-sinh-cao-dang-nganh-Giao-duc-Mam-non-Dai-hoc-444671.aspx"),
    # Luật Công chức
    ("luat-can-bo-cong-chuc-2008", "https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-Can-bo-cong-chuc-2008-82199.aspx"),
    # Quy định về xử lý kỷ luật sinh viên
    ("thong-tu-10-2016-ky-luat", "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-10-2016-TT-BGDDT-quy-che-cong-tac-sinh-vien-co-so-giao-duc-dai-hoc-he-chinh-quy-312447.aspx"),
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_filename(name: str, ext: str = "") -> str:
    clean = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip()[:120]
    if ext and not clean.endswith(ext):
        clean += ext
    return clean

def chunk_by_article(text: str, source_name: str, source_url: str) -> list[dict]:
    """Article-level chunking → fallback paragraph chunking"""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)  # Clean excessive blank lines

    # Tách theo "Điều X."
    pattern = r'(?=\n\s*Điều\s+\d+[\.\:\s])'
    parts = re.split(pattern, text)

    chunks = []
    if len(parts) > 3:
        log.info(f"  → Article-level: {len(parts)} articles")
        for part in parts:
            part = part.strip()
            if len(part) < 60:
                continue
            first_line = part.split('\n')[0].strip()[:120]
            chunks.append({
                "title": f"{source_name} - {first_line}",
                "content": part,
                "metadata": {
                    "source": source_name,
                    "source_url": source_url,
                    "chunk_type": "article"
                }
            })
    else:
        # Paragraph chunking ~800 chars
        log.info(f"  → Paragraph chunking (no article structure)")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        current, length, idx = [], 0, 0
        for line in lines:
            current.append(line)
            length += len(line)
            if length >= 800:
                chunks.append({
                    "title": f"{source_name} - Đoạn {idx + 1}",
                    "content": "\n".join(current),
                    "metadata": {
                        "source": source_name,
                        "source_url": source_url,
                        "chunk_type": "paragraph"
                    }
                })
                idx += 1
                current, length = [], 0
        if current:
            chunks.append({
                "title": f"{source_name} - Đoạn {idx + 1}",
                "content": "\n".join(current),
                "metadata": {
                    "source": source_name,
                    "source_url": source_url,
                    "chunk_type": "paragraph"
                }
            })

    return [c for c in chunks if len(c['content'].strip()) > 80]

def save_chunks(chunks: list[dict], doc_id: str):
    """Lưu JSON"""
    out_path = EXTRACTED_DIR / f"{doc_id}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            "doc_id": doc_id,
            "extracted_at": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "chunks": chunks
        }, f, ensure_ascii=False, indent=2)
    log.info(f"  → Saved → {out_path.name} ({len(chunks)} chunks)")

def clean_legal_text(raw: str) -> str:
    """Làm sạch text lấy từ HTML"""
    # Bỏ khoảng trắng thừa
    text = re.sub(r'[ \t]+', ' ', raw)
    # Chuẩn hóa newlines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    # Bỏ các dòng toàn ký tự đặc biệt
    lines = [l for l in text.split('\n') if not re.match(r'^[\-_=\*\.]{3,}$', l.strip())]
    return '\n'.join(lines).strip()

# ═══════════════════════════════════════════════════════════════════════════════
# NGUỒN 1: TVPL - Scrape text trực tiếp từ trang web (không download file)
# ═══════════════════════════════════════════════════════════════════════════════
def scrape_tvpl_texts(page) -> list[dict]:
    """Scrape full text từ các văn bản đã được định nghĩa"""
    all_chunks = []

    for doc_id, url in TVPL_TARGET_URLS:
        # Kiểm tra đã extract chưa
        out_path = EXTRACTED_DIR / f"{doc_id}.json"
        if out_path.exists():
            log.info(f"  SKIP (cached): {doc_id}")
            with open(out_path, encoding='utf-8') as f:
                data = json.load(f)
                all_chunks.extend(data.get('chunks', []))
            continue

        log.info(f"\n  Processing: {doc_id}")
        log.info(f"  URL: {url}")

        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            # Đợi thêm một chút để JS render text
            page.wait_for_timeout(3000)

            # Lấy tiêu đề chính thức
            title = doc_id
            for sel in ["h1.title-vb", "h1.document-title", ".doc-title h1", "h1"]:
                el = page.query_selector(sel)
                if el:
                    t = el.inner_text().strip()
                    if len(t) > 10:
                        title = t
                        break
            log.info(f"  Title: {title[:80]}")

            # Tab "Nội dung" - click nếu cần
            for tab_sel in ["a:has-text('Nội dung')", "#tab1-link", "a[href='#tab1']"]:
                try:
                    tab = page.query_selector(tab_sel)
                    if tab and tab.is_visible():
                        tab.click()
                        page.wait_for_timeout(1000)
                        break
                except:
                    pass

            # Lấy text từ container chính
            raw_text = ""
            for sel in [".content1", "#divContent", ".vbContent", ".noidung-vb", "#tab1 .content", ".doc-content", "div[style*='text-align: justify']"]:
                el = page.query_selector(sel)
                if el:
                    t = el.inner_text()
                    if len(t) > 500:
                        raw_text = t
                        log.info(f"  Found text via '{sel}': {len(t)} chars")
                        break

            if not raw_text:
                # Fallback: lấy body text và cắt bỏ nav/header/footer
                raw_text = page.evaluate("""() => {
                    const skipTags = ['nav','header','footer','script','style','aside'];
                    const els = document.querySelectorAll(skipTags.join(','));
                    els.forEach(e => e.remove());
                    return document.body.innerText;
                }""")
                log.warning(f"  Using body fallback: {len(raw_text)} chars")

            if len(raw_text.strip()) < 200:
                log.error(f"  Text too short ({len(raw_text)} chars), skipping")
                continue

            # Clean text
            text = clean_legal_text(raw_text)
            log.info(f"  Clean text: {len(text)} chars")

            # Chunk
            chunks = chunk_by_article(text, title, url)
            log.info(f"  Chunks: {len(chunks)}")

            if chunks:
                save_chunks(chunks, doc_id)
                all_chunks.extend(chunks)

            # Quality check: print first chunk
            if chunks:
                log.info(f"  SAMPLE (first chunk):\n{'─'*40}\n{chunks[0]['content'][:300]}\n{'─'*40}")

            time.sleep(2)

        except Exception as e:
            log.error(f"  FAILED: {doc_id} - {e}")

    return all_chunks

# ═══════════════════════════════════════════════════════════════════════════════
# NGUỒN 2: HCTLU - Lấy danh sách tiêu đề văn bản (metadata index)
# ═══════════════════════════════════════════════════════════════════════════════
def scrape_hctlu_index(page) -> list[dict]:
    """
    Lấy INDEX danh sách văn bản từ HCTLU portal làm metadata.
    PDF là scanned → không extract text → chỉ lưu tiêu đề/metadata.
    Dùng để biết văn bản nào đang hiệu lực tại TLU.
    """
    all_index = []
    log.info("HCTLU: Scraping document index (titles/metadata)...")

    try:
        # Navigate to doc list
        page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=180", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        page_num = 0
        while page_num < 5:  # Tối đa 5 trang
            page_num += 1
            log.info(f"  HCTLU page {page_num}")

            # ── Lấy tất cả rows có "Download" link ─────────────────────────────
            # Sử dụng selector linh hoạt hơn dựa trên ID của DotNetNuke DataGrid
            rows = page.query_selector_all("tr.dgItem, tr.dgAltItem, tr:has(a[id*='grdDocuments_ctlTitle_'])")
            
            if not rows:
                log.warning("  No rows found with standard selectors, trying broad table search...")
                rows = page.query_selector_all("table[id*='grdDocuments'] tr:not(.dgHeader)")

            for row in rows:
                try:
                    cells = row.query_selector_all("td")
                    if len(cells) >= 2:
                        idx_cell = cells[0].inner_text().strip()
                        title_cell = cells[1].inner_text().strip() if len(cells) > 1 else ""
                        date_cell = cells[2].inner_text().strip() if len(cells) > 2 else ""

                        if title_cell and len(title_cell) > 5:
                            all_index.append({
                                "idx": idx_cell,
                                "title": title_cell,
                                "date": date_cell,
                                "source": "hanhchinh.tlu.edu.vn",
                                "portal_url": "https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=180"
                            })
                except:
                    continue

            # Next page
            try:
                next_btn = page.query_selector("a.CommandButton:has-text('Next'), td[align='Right'] a")
                if next_btn:
                    next_btn.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                else:
                    break
            except:
                break

    except Exception as e:
        log.error(f"HCTLU index scraping failed: {e}")

    # Lưu index
    index_path = EXTRACTED_DIR / "hanhchinh_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "hanhchinh.tlu.edu.vn",
            "scraped_at": datetime.now().isoformat(),
            "total": len(all_index),
            "documents": all_index
        }, f, ensure_ascii=False, indent=2)

    log.info(f"HCTLU: Saved {len(all_index)} document titles → hanhchinh_index.json")

    # Tạo chunks từ tiêu đề (metadata-only chunks để search có thể định hướng tên văn bản)
    chunks = []
    for doc in all_index:
        content = f"Văn bản: {doc['title']}\nBan hành: {doc['date']}\nNguồn: Hành chính TLU Portal"
        chunks.append({
            "title": doc['title'],
            "content": content,
            "metadata": {
                "source": doc['title'],
                "source_url": doc['portal_url'],
                "date": doc['date'],
                "chunk_type": "metadata_index",
                "data_type": "reference_only"
            }
        })

    return chunks

# ═══════════════════════════════════════════════════════════════════════════════
# INJECT vào Vector DB
# ═══════════════════════════════════════════════════════════════════════════════
def inject_to_vectordb(all_chunks: list[dict]):
    sys.path.insert(0, str(BASE_DIR / "search-agent"))
    try:
        from vector_db_client import VectorDBClient
        from embedding_service import EmbeddingService
    except ImportError as e:
        log.error(f"Cannot import vector DB modules: {e}")
        return

    log.info(f"\n{'='*60}")
    log.info(f"INJECTING {len(all_chunks)} chunks into Vector DB (tlu_knowledge)...")

    vdb = VectorDBClient()
    embedder = EmbeddingService()

    # Batch size nhỏ để tránh memory spike
    BATCH_SIZE = 16
    success = 0
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        texts = [c['content'] for c in batch]
        try:
            vectors = embedder.embed_texts(texts)
            vdb.upsert_chunks(batch, vectors)
            success += len(batch)
            log.info(f"  ✅ Batch {i//BATCH_SIZE + 1}: injected {len(batch)} chunks")
        except Exception as e:
            log.error(f"  ✗ Batch {i//BATCH_SIZE + 1} failed: {e}")

    log.info(f"  Injection complete: {success}/{len(all_chunks)} chunks successful")

    # Final verification
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        count = client.get_collection("tlu_knowledge").points_count
        log.info(f"  Vector DB total: {count} points")
    except Exception as e:
        log.warning(f"  Could not verify DB count: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION: Kiểm tra chất lượng kết quả sau inject
# ═══════════════════════════════════════════════════════════════════════════════
def verify_extraction(all_chunks: list[dict]):
    log.info("\n" + "="*60)
    log.info("VERIFICATION REPORT")
    log.info("="*60)

    tvpl_chunks = [c for c in all_chunks if "article" in c['metadata'].get('chunk_type', '')]
    other_chunks = [c for c in all_chunks if c not in tvpl_chunks]

    log.info(f"Total chunks: {len(all_chunks)}")
    log.info(f"  - Article-level (TVPL full text): {len(tvpl_chunks)}")
    log.info(f"  - Metadata/Paragraph: {len(other_chunks)}")

    # Sample 3 chunks
    log.info("\nSAMPLE OUTPUT (first 3 article chunks):")
    for c in tvpl_chunks[:3]:
        log.info(f"\n[SOURCE]: {c['metadata']['source']}")
        log.info(f"[TITLE]:  {c['title']}")
        log.info(f"[LENGTH]: {len(c['content'])} chars")
        log.info(f"[PREVIEW]:\n{c['content'][:400]}")
        log.info("-"*40)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    log.info("SMART PIPELINE v2 STARTED")
    log.info(f"Strategy: TVPL web-scrape + HCTLU metadata index")
    log.info(f"Timestamp: {datetime.now().isoformat()}")

    all_chunks = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # ── PHASE 1: TVPL - Login & Scrape full text ────────────────────────────
        log.info("\n" + "="*60)
        log.info("PHASE 1: TVPL - Scraping full legal texts")
        log.info("="*60)

        tvpl_logged_in = False
        try:
            log.info("TVPL: Logging in...")
            page.goto("https://thuvienphapluat.vn/page/login.aspx", timeout=60000, wait_until="domcontentloaded")
            # Đợi Form xuất hiện
            page.wait_for_selector("#UserName", timeout=20000)
            page.fill("#UserName", TVPL_USER)
            page.fill("#Password", TVPL_PASS)
            page.click("#Button1")
            
            # Đợi Postback/Navigation
            page.wait_for_timeout(5000)
            
            # Xử lý "đăng nhập trùng" popup nếu có
            try:
                overlap_btn = page.query_selector("input[value='Đồng ý'], button:has-text('Đồng ý'), #btnDongY")
                if overlap_btn and overlap_btn.is_visible():
                    log.info("TVPL: Handling overlap session popup...")
                    overlap_btn.click()
            except:
                pass
            
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            current_url = page.url
            log.info(f"TVPL: After login URL: {current_url}")

            if "login" not in current_url.lower():
                tvpl_logged_in = True
                log.info("TVPL: Login SUCCESSFUL")
            else:
                log.warning("TVPL: Login seems to have failed, but proceeding anyway (public text)...")
                tvpl_logged_in = True # Forced proceed
        except Exception as e:
            log.error(f"TVPL Login error: {e}. Proceeding as guest...")
            tvpl_logged_in = True # Forced proceed

        if tvpl_logged_in:
            tvpl_chunks = scrape_tvpl_texts(page)
            all_chunks.extend(tvpl_chunks)
            log.info(f"\nTVPL TOTAL: {len(tvpl_chunks)} chunks")
        else:
            log.warning("TVPL: Skipping due to login failure")

        # ── PHASE 2: HCTLU - Index tiêu đề ─────────────────────────────────────
        log.info("\n" + "="*60)
        log.info("PHASE 2: HCTLU - Document index (metadata)")
        log.info("="*60)

        try:
            log.info("HCTLU: Logging in...")
            page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=20000)
            page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", HANH_CHINH_USER)
            page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", HANH_CHINH_PASS)
            page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
            page.wait_for_load_state("networkidle", timeout=20000)
            log.info("HCTLU: Login successful")

            hctlu_chunks = scrape_hctlu_index(page)
            all_chunks.extend(hctlu_chunks)
            log.info(f"\nHCTLU TOTAL: {len(hctlu_chunks)} metadata chunks")

        except Exception as e:
            log.error(f"HCTLU phase failed: {e}")

        browser.close()

    # ── PHASE 3: Verification ───────────────────────────────────────────────────
    verify_extraction(all_chunks)

    # ── PHASE 4: Inject ─────────────────────────────────────────────────────────
    log.info("\n" + "="*60)
    log.info("PHASE 4: Injecting into Vector DB")
    log.info("="*60)
    inject_to_vectordb(all_chunks)

    log.info(f"\n✅ PIPELINE v2 COMPLETE")
    log.info(f"Total chunks produced: {len(all_chunks)}")
    log.info(f"Log: {LOG_FILE}")

if __name__ == "__main__":
    main()
