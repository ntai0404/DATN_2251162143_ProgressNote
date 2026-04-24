"""
Smart Collector Pipeline - Tuần 3-5
Nguồn 1: hanhchinh.tlu.edu.vn (TabID 180)  → Download → PDF fallback
Nguồn 2: thuvienphapluat.vn                → DOC/DOCX ưu tiên → PDF fallback

Chiến lược:
- TVPL: Tab "Tải về" → lấy "Tải Văn bản tiếng Việt" (DOC) trước, 
  nếu không có thì lấy "Văn bản gốc" (PDF).
- HCTLU: Chỉ có 1 link Download/row → download thẳng, 
  kiểm tra extension để biết loại.
- Sau khi tải: extract text ngay (DOCX dùng python-docx, PDF dùng fitz).
- Nếu fitz trả empty (scanned PDF) → đánh dấu cần OCR, bỏ qua tạm.
- Lưu kết quả ra data_extracted/{source_name}/{filename}.json
"""

import os
import sys
import re
import time
import json
import logging
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent          # taskweek3-5/
EXTRACTED_DIR = BASE_DIR / "data_extracted"
RAW_DIR = BASE_DIR / "data_raw"
LOG_FILE = BASE_DIR / "smart_pipeline.log"
ENV_FILE = Path(__file__).parent / ".env"

EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("smart-pipeline")

load_dotenv(ENV_FILE)

HANH_CHINH_USER = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
HANH_CHINH_PASS = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")
TVPL_USER = os.getenv("THU_VIEN_PHAP_LUAT_USER", "P2")
TVPL_PASS = os.getenv("THU_VIEN_PHAP_LUAT_PASS", "dhtl123456")

# ── TVPL document URLs liên quan đến TLU ─────────────────────────────────────
# Đây là danh sách URL trang của các văn bản pháp luật liên quan đến giáo dục ĐH
TVPL_DOCUMENT_URLS = [
    # Luật Giáo dục đại học 2012
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-dai-hoc-2012-141398.aspx",
    # Luật sửa đổi GDĐH 2018
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-sua-doi-Luat-Giao-duc-dai-hoc-2018-371747.aspx",
    # Quy chế đào tạo đại học (Thông tư 08)
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-08-2021-TT-BGDDT-quy-che-dao-tao-trinh-do-dai-hoc-468368.aspx",
    # Nghị định 99 học phí (URL Updated)
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Nghi-dinh-99-2019-ND-CP-huong-dan-Luat-Giao-duc-dai-hoc-432906.aspx",
    # Thông tư 10 học bổng (URL Updated)
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-10-2016-TT-BGDDT-quy-che-cong-tac-sinh-vien-co-so-giao-duc-dai-hoc-he-chinh-quy-308119.aspx",
    # Luật Viên chức
    "https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-Vien-chuc-2010-107730.aspx",
    # Luật Giáo dục 2019
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-Giao-duc-2019-333172.aspx",
]

def safe_filename(name: str, ext: str = "") -> str:
    """Làm sạch tên file"""
    clean = re.sub(r'[<>:"/\\|?*]', '_', name).strip()
    clean = clean[:120]
    if ext and not clean.endswith(ext):
        clean += ext
    return clean

def extract_text_from_docx(file_path: Path) -> str:
    """Trích xuất text từ DOCX - chuẩn 100%"""
    try:
        from docx import Document
        doc = Document(str(file_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        # Gộp các đoạn giữ cấu trúc
        return "\n\n".join(paragraphs)
    except Exception as e:
        log.error(f"DOCX extraction failed: {e}")
        return ""

def extract_text_from_pdf(file_path: Path) -> tuple[str, bool]:
    """
    Trích xuất text từ PDF bằng fitz.
    Returns: (text, is_scanned)
    - is_scanned=True nếu PDF là ảnh quét (cần OCR)
    """
    try:
        import fitz
        doc = fitz.open(str(file_path))
        pages_text = []
        for page in doc:
            t = page.get_text().strip()
            if t:
                pages_text.append(t)
        
        full_text = "\n\n".join(pages_text)
        
        if len(full_text.strip()) < 100:
            return "", True  # Scanned PDF - cần OCR
        return full_text, False
    except Exception as e:
        log.error(f"PDF extraction failed: {e}")
        return "", True

def chunk_by_article(text: str, source_name: str, file_type: str) -> list[dict]:
    """
    Chia text theo cấu trúc Điều/Khoản (Article-level chunking).
    Nếu không có cấu trúc Điều, chia theo đoạn 800 ký tự.
    """
    # Chuẩn hóa unicode
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Tách theo "Điều X"
    pattern = r'(?=\n\s*Điều\s+\d+[\.\:])'
    parts = re.split(pattern, text)
    
    chunks = []
    if len(parts) > 2:
        log.info(f"  → Article-level chunking: {len(parts)} articles found")
        for part in parts:
            part = part.strip()
            if len(part) > 80:
                # Lấy tiêu đề Điều đầu tiên làm title
                first_line = part.split('\n')[0].strip()
                chunks.append({
                    "title": f"{source_name} - {first_line}",
                    "content": part,
                    "metadata": {
                        "source": source_name,
                        "file_type": file_type,
                        "chunk_type": "article"
                    }
                })
    else:
        # Fallback: chia theo đoạn văn ~800 ký tự
        log.info(f"  → Paragraph-level chunking (no article structure detected)")
        sentences = [s.strip() for s in text.split('\n') if s.strip()]
        current_chunk = []
        current_len = 0
        chunk_idx = 0
        
        for sentence in sentences:
            current_chunk.append(sentence)
            current_len += len(sentence)
            if current_len >= 800:
                chunk_text = "\n".join(current_chunk)
                chunks.append({
                    "title": f"{source_name} - Đoạn {chunk_idx + 1}",
                    "content": chunk_text,
                    "metadata": {
                        "source": source_name,
                        "file_type": file_type,
                        "chunk_type": "paragraph"
                    }
                })
                chunk_idx += 1
                current_chunk = []
                current_len = 0
        
        if current_chunk:
            chunks.append({
                "title": f"{source_name} - Đoạn {chunk_idx + 1}",
                "content": "\n".join(current_chunk),
                "metadata": {
                    "source": source_name,
                    "file_type": file_type,
                    "chunk_type": "paragraph"
                }
            })
    
    return [c for c in chunks if len(c['content'].strip()) > 50]

def save_chunks(chunks: list[dict], source_tag: str, doc_name: str):
    """Lưu chunks ra file JSON"""
    out_dir = EXTRACTED_DIR / source_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    
    uid = hashlib.md5(doc_name.encode()).hexdigest()[:8]
    out_path = out_dir / f"{safe_filename(doc_name)}_{uid}.json"
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            "document": doc_name,
            "source": source_tag,
            "extracted_at": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "chunks": chunks
        }, f, ensure_ascii=False, indent=2)
    
    log.info(f"  → Saved {len(chunks)} chunks → {out_path.name}")
    return out_path

def process_file(file_path: Path, source_name: str, source_tag: str) -> list[dict]:
    """
    Phân tích file và trả về danh sách chunks.
    Tự động detect loại file.
    """
    ext = file_path.suffix.lower()
    
    if ext in ['.docx', '.doc']:
        log.info(f"  ↳ Extracting DOCX (text-native): {file_path.name}")
        text = extract_text_from_docx(file_path)
        if not text:
            log.warning(f"  ↳ DOCX returned empty text, skipping: {file_path.name}")
            return []
        file_type = "docx"
    elif ext == '.pdf':
        log.info(f"  ↳ Extracting PDF: {file_path.name}")
        text, is_scanned = extract_text_from_pdf(file_path)
        if is_scanned:
            log.warning(f"  ↳ SCANNED PDF (no text layer) - needs OCR later: {file_path.name}")
            # Đánh dấu trong log để xử lý OCR sau
            with open(BASE_DIR / "needs_ocr.txt", 'a', encoding='utf-8') as f:
                f.write(str(file_path) + "\n")
            return []
        file_type = "pdf"
    else:
        log.warning(f"  ↳ Unsupported format: {ext}")
        return []
    
    log.info(f"  ↳ Extracted {len(text)} chars, chunking...")
    chunks = chunk_by_article(text, source_name, file_type)
    
    if chunks:
        save_chunks(chunks, source_tag, source_name)
    
    return chunks

# ═══════════════════════════════════════════════════════════════════════════════
# NGUỒN 1: Thư viện Pháp luật (DOC-first)
# ═══════════════════════════════════════════════════════════════════════════════
def harvest_tvpl():
    """
    Thu thập từ thuvienphapluat.vn.
    Ưu tiên: "Tải Văn bản tiếng Việt" (DOC) → fallback "Văn bản gốc" (PDF)
    """
    log.info("=" * 60)
    log.info("NGUỒN 1: THƯ VIỆN PHÁP LUẬT (DOC-FIRST STRATEGY)")
    log.info("=" * 60)
    
    out_dir = RAW_DIR / "tvpl"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        def get_fresh_page():
            context = browser.new_context(
                accept_downloads=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            return context, context.new_page()

        context, page = get_fresh_page()
        
        # ── Đăng nhập ──────────────────────────────────────────────────────────
        log.info("TVPL: Logging in...")
        try:
            page.goto("https://thuvienphapluat.vn/page/login.aspx", timeout=60000)
            page.wait_for_selector("#UserName", timeout=30000)
            page.fill("#UserName", TVPL_USER)
            page.fill("#Password", TVPL_PASS)
            page.click("#Button1")
            
            # Xử lý overlap session hoặc popup cảnh báo
            page.wait_for_timeout(5000)
            agree_btn = page.locator("input[value*='Đồng ý'], button:has-text('Đồng ý'), #btnDongY, .btnAgree").first
            if agree_btn.is_visible():
                log.info("TVPL: Overlap detected. Confirming session...")
                agree_btn.click()
                page.wait_for_timeout(3000)
            
            log.info("TVPL: Login successful")
        except Exception as e:
            log.error(f"TVPL Login failed: {e}")
            browser.close()
            return all_chunks
        
        # ── Thu thập từng văn bản ───────────────────────────────────────────────
        for doc_url in TVPL_DOCUMENT_URLS:
            try:
                log.info(f"\nTVPL: Processing → {doc_url}")
                page.goto(doc_url, timeout=60000)
                # Chờ Cloudflare hoặc trang load hẳn
                page.wait_for_timeout(10000) 
                
                # Lấy tiêu đề văn bản chuẩn từ URL nếu tiêu đề trang bị rác
                doc_title = ""
                title_h1 = page.locator("h1.title-vb, h1").first
                if title_h1.is_visible(timeout=5000):
                    doc_title = title_h1.inner_text().strip()
                
                # Kiểm tra xem có bị trúng "Bẫy" không (Title khác hẳn nội dung URL)
                page_title_low = page.title().lower()
                if "just a moment" in page_title_low or "thuvienphapluat" in doc_title.lower() or not doc_title:
                    log.warning(f"  ⚠️ Detection triggered or Page not loaded. Retrying with fresh context...")
                    context.close()
                    context, page = get_fresh_page()
                    # Re-login might be needed, but let's try direct access first
                    page.goto(doc_url, timeout=60000)
                    page.wait_for_timeout(15000)
                    title_h1 = page.locator("h1.title-vb, h1").first
                    if title_h1.is_visible(timeout=5000):
                        doc_title = title_h1.inner_text().strip()

                if not doc_title or "thuvienphapluat" in doc_title.lower():
                    # Fallback cuối cùng: Lấy từ slug của URL
                    doc_title = doc_url.split('/')[-1].replace('.aspx', '')

                log.info(f"  Actual Title: {doc_title[:80]}")
                
                # ── Tìm tab "Tải về" ────────────────────────────────────────────
                tab_selectors = [
                    "ul.nav-tabs-vb li:has-text('Tải về')",
                    "ul.nav-tabs-vb li:has-text('Văn bản gốc/PDF')",
                    "a:has-text('Tải về')",
                    "a:has-text('Văn bản gốc/PDF')"
                ]
                
                tab_download = None
                for selector in tab_selectors:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=5000):
                        tab_download = loc
                        break
                
                if tab_download:
                    log.info(f"  Opening Download Tab...")
                    tab_download.click()
                    page.wait_for_timeout(4000)
                
                downloaded_file = None
                file_type_label = "doc"
                online_text = ""
                
                # ── BƯỚC 1: Lấy nội dung text online trước (để đảm bảo có dữ liệu) ─────
                try:
                    content_el = page.locator("#ctl00_Content_ThongTinVB_divNoiDung, .content-vb").first
                    if content_el.is_visible(timeout=10000):
                        online_text = content_el.inner_text().strip()
                        log.info(f"  ✅ Online text captured ({len(online_text)} chars)")
                except:
                    log.warning("  Could not capture online text.")

                # ── BƯỚC 2: Tải file DOC theo yêu cầu USER ──────────────────────────
                try:
                    doc_link = page.locator(
                        "#ctl00_Content_ThongTinVB_vietnameseHyperLink, "
                        "a[id*='vietnameseHyperLink'], "
                        "a:has-text('Tải Văn bản tiếng Việt'), "
                        "a:has-text('Tải văn bản (.doc)')"
                    ).first
                    if doc_link.is_visible(timeout=5000):
                        log.info(f"  → DOC link found, downloading...")
                        with page.expect_download(timeout=60000) as dl:
                            doc_link.click()
                        download = dl.value
                        ext = Path(download.suggested_filename).suffix or ".doc"
                        out_path = out_dir / safe_filename(doc_title, ext)
                        download.save_as(str(out_path))
                        downloaded_file = out_path
                        log.info(f"  ✅ DOC downloaded: {out_path.name} ({out_path.stat().st_size} bytes)")
                except Exception as e:
                    log.warning(f"  DOC download failed: {e}")
                
                # ── BƯỚC 3: Xử lý nội dung ──────────────────────────────────────────
                chunks = []
                if downloaded_file and downloaded_file.suffix.lower() == ".docx":
                    # Chỉ dùng python-docx cho .docx
                    chunks = process_file(downloaded_file, doc_title, "tvpl")
                
                # Nếu không có chunks từ file (vì là .doc cũ hoặc lỗi), dùng online_text
                if not chunks and online_text:
                    log.info(f"  → Falling back to online text for chunking...")
                    chunks = chunk_by_article(online_text, doc_title, "web_scrape")
                    if chunks:
                        save_chunks(chunks, "tvpl", doc_title)
                
                if chunks:
                    all_chunks.extend(chunks)
                    log.info(f"  → Produced {len(chunks)} chunks")
                else:
                    log.error(f"  ✗ Could not extract content for: {doc_title}")
                
                time.sleep(2)  # Tránh bị rate limit
                
            except Exception as e:
                log.error(f"TVPL: Failed for {doc_url}: {e}")
        
        browser.close()
    
    log.info(f"\nTVPL TOTAL: {len(all_chunks)} chunks extracted")
    return all_chunks

# ═══════════════════════════════════════════════════════════════════════════════
# NGUỒN 2: Hành chính TLU (PDF → extract, flag scanned)
# ═══════════════════════════════════════════════════════════════════════════════
def harvest_hanhchinh(max_pages: int = 5):
    """
    Thu thập từ hanhchinh.tlu.edu.vn TabID 180.
    Mỗi row chỉ có 1 link Download → tải về, kiểm tra text.
    Nếu PDF có text → extract ngay. Nếu không → đánh dấu OCR.
    max_pages: số trang cần duyệt (mỗi trang ~20 văn bản)
    """
    log.info("\n" + "=" * 60)
    log.info("NGUỒN 2: HÀNH CHÍNH TLU (hanhchinh.tlu.edu.vn)")
    log.info("=" * 60)
    
    out_dir = RAW_DIR / "hanhchinh"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        # ── Đăng nhập ──────────────────────────────────────────────────────────
        log.info("HCTLU: Logging in...")
        try:
            page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74", timeout=30000)
            page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", HANH_CHINH_USER)
            page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", HANH_CHINH_PASS)
            page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
            page.wait_for_load_state("networkidle", timeout=20000)
            log.info("HCTLU: Login successful")
        except Exception as e:
            log.error(f"HCTLU Login failed: {e}")
            browser.close()
            return all_chunks
        
        # ── Vào trang Văn bản quản lý (tabid=180) ──────────────────────────────
        log.info("HCTLU: Navigating to Văn bản quản lý (tabid=180)...")
        page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=180", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)
        
        page_num = 0
        total_downloaded = 0
        
        while page_num < max_pages:
            page_num += 1
            log.info(f"\nHCTLU: Processing page {page_num}...")
            
            # ── Lấy tất cả rows có "Download" link ─────────────────────────────
            rows = page.query_selector_all("tr.dgItem, tr.dgAltItem")
            if not rows:
                rows = page.query_selector_all("table tr")
            
            log.info(f"  Found {len(rows)} document rows on this page")
            
            # Lấy thông tin từng row trước (không click liền vì DOM sẽ thay đổi)
            row_data = []
            for row in rows:
                try:
                    # Lấy title từ cột đầu tiên
                    title_cell = row.query_selector("td:nth-child(1) a, td:nth-child(2) a")
                    dl_link = row.query_selector("a[id*='DownloadLink'], a:has-text('Download')")
                    
                    if dl_link and title_cell:
                        title = title_cell.inner_text().strip()
                        dl_href = dl_link.get_attribute("href") or ""
                        row_data.append({
                            "title": title,
                            "dl_href": "https://hanhchinh.tlu.edu.vn" + dl_href if dl_href.startswith("/") else dl_href
                        })
                except:
                    continue
            
            log.info(f"  Extracted {len(row_data)} download targets")
            
            # ── Download từng file ──────────────────────────────────────────────
            for item in row_data:
                title = item["title"]
                dl_href = item["dl_href"]
                
                if not title or not dl_href:
                    continue
                
                # Kiểm tra đã tải chưa
                check_path_pdf = out_dir / safe_filename(title, ".pdf")
                check_path_doc = out_dir / safe_filename(title, ".docx")
                if check_path_pdf.exists() or check_path_doc.exists():
                    log.info(f"  SKIP (exists): {title[:50]}")
                    continue
                
                log.info(f"  Downloading: {title[:60]}")
                try:
                    with page.expect_download(timeout=60000) as dl_info:
                        page.evaluate(f"window.open('{dl_href}', '_self')")
                    download = dl_info.value
                    
                    suggested = download.suggested_filename
                    ext = Path(suggested).suffix.lower() if suggested else ".pdf"
                    if ext not in ['.pdf', '.doc', '.docx']:
                        ext = ".pdf"
                    
                    out_path = out_dir / safe_filename(title, ext)
                    download.save_as(str(out_path))
                    size = out_path.stat().st_size
                    log.info(f"  ✅ Downloaded: {out_path.name} ({size / 1024:.1f} KB)")
                    total_downloaded += 1
                    
                    # Extract ngay
                    chunks = process_file(out_path, title, "hanhchinh")
                    all_chunks.extend(chunks)
                    if chunks:
                        log.info(f"  → Produced {len(chunks)} chunks from {ext.upper()}")
                    
                    time.sleep(1.5)
                    
                except Exception as e:
                    log.error(f"  ✗ Download failed: {title[:50]} - {e}")
            
            # ── Chuyển trang tiếp theo ──────────────────────────────────────────
            try:
                next_btn = page.query_selector("a.CommandButton:has-text('Next'), a[href*='page=']:has-text('>'), a:has-text('Trang sau')")
                if next_btn:
                    next_btn.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    log.info("  → Navigated to next page")
                else:
                    log.info("  → No more pages found")
                    break
            except:
                log.info("  → Could not find next page button, stopping")
                break
        
        log.info(f"\nHCTLU TOTAL: {total_downloaded} files downloaded, {len(all_chunks)} chunks extracted")
        browser.close()
    
    return all_chunks

# ═══════════════════════════════════════════════════════════════════════════════
# INJECT vào Vector DB
# ═══════════════════════════════════════════════════════════════════════════════
def inject_to_vectordb(all_chunks: list[dict]):
    """Đẩy toàn bộ chunks vào Qdrant"""
    if not all_chunks:
        log.warning("No chunks to inject.")
        return
    
    sys.path.insert(0, str(BASE_DIR / "search-agent"))
    from vector_db_client import VectorDBClient
    from embedding_service import EmbeddingService
    
    log.info(f"\n{'='*60}")
    log.info(f"INJECTING {len(all_chunks)} chunks into Vector DB...")
    
    vdb = VectorDBClient()
    embedder = EmbeddingService()
    
    # Batch embedding để tiết kiệm memory
    BATCH_SIZE = 32
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        texts = [c['content'] for c in batch]
        try:
            vectors = embedder.embed_texts(texts)
            vdb.upsert_chunks(batch, vectors)
            log.info(f"  Injected batch {i//BATCH_SIZE + 1}: {len(batch)} chunks")
        except Exception as e:
            log.error(f"  Batch injection failed: {e}")
    
    # Verify count
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        count = client.get_collection("tlu_knowledge").points_count
        log.info(f"  ✅ Vector DB now has {count} total points")
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    log.info("SMART PIPELINE STARTED")
    log.info(f"Timestamp: {datetime.now().isoformat()}")
    
    all_chunks = []
    
    # Chạy song song 2 nguồn (sequential vì playwright)
    log.info("\n>>> PHASE 1: Collecting from Thư viện Pháp luật...")
    tvpl_chunks = harvest_tvpl()
    all_chunks.extend(tvpl_chunks)
    
    log.info("\n>>> PHASE 2: Collecting from Hành chính TLU...")
    hctlu_chunks = harvest_hanhchinh(max_pages=3)  # Bắt đầu với 3 trang (~60 văn bản)
    all_chunks.extend(hctlu_chunks)
    
    log.info(f"\n{'='*60}")
    log.info(f"TOTAL CHUNKS COLLECTED: {len(all_chunks)}")
    log.info(f"  - TVPL:     {len(tvpl_chunks)}")
    log.info(f"  - HCTLU:    {len(hctlu_chunks)}")
    
    # Phase 3: Inject vào DB
    log.info("\n>>> PHASE 3: Injecting into Vector DB...")
    inject_to_vectordb(all_chunks)
    
    log.info("\n✅ SMART PIPELINE COMPLETE")
    log.info(f"Log file: {LOG_FILE}")
    
    # Báo cáo OCR needs
    ocr_file = BASE_DIR / "needs_ocr.txt"
    if ocr_file.exists():
        with open(ocr_file, encoding='utf-8') as f:
            lines = f.readlines()
        log.info(f"\n⚠️  {len(lines)} scanned PDFs need OCR → see {ocr_file}")

if __name__ == "__main__":
    main()
