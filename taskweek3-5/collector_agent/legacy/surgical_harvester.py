import os
import time
import json
import sys
import re
from playwright.sync_api import sync_playwright
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def clean_filename_v3(title_raw):
    # 1. Loại bỏ các ký tự rác và khoảng trắng thừa
    title_clean = " ".join(title_raw.split())
    # 2. Loại bỏ đuôi .pdf nếu có trong text gốc
    title_clean = re.sub(r'\.pdf$', '', title_clean, flags=re.IGNORECASE)
    # 3. Trích xuất năm
    year_match = re.search(r'\d{4}', title_clean)
    year = year_match.group(0) if year_match else ""
    
    # 4. Xóa năm khỏi title để tránh lặp lại (ví dụ "(2021) 2021 ...")
    title_no_year = title_clean
    if year:
        title_no_year = title_clean.replace(year, "").strip()
    
    # 5. Loại bỏ ký tự đặc biệt
    safe_title = re.sub(r'[^\w\s-]', '', title_no_year).strip()
    safe_title = re.sub(r'\s+', ' ', safe_title)
    
    # 6. Ghép tên cuối cùng: (Năm) Tên văn bản.pdf
    if year:
        final_name = f"({year}) {safe_title}.pdf"
    else:
        final_name = f"{safe_title}.pdf"
        
    return final_name.replace(' .pdf', '.pdf')

def surgical_harvest_v3():
    """Trình thu thập TLU Admin v3: Đặt tên siêu sạch và quản lý metadata chuẩn"""
    user = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
    password = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")
    
    base_dir = Path(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5")
    download_dir = base_dir / "data_raw" / "hanhchinh"
    metadata_dir = base_dir / "data_extracted" / "metadata"
    
    # Dọn dẹp các file rác trước khi chạy (Optional nhưng nên làm để sạch sẽ)
    for f in download_dir.glob("*.pdf.pdf"): f.unlink()
    for f in download_dir.glob("*(202*)*202*.pdf"): f.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74", timeout=60000)
            page.fill("#dnn_ctr_Login_Login_DNN_txtUsername", user)
            page.fill("#dnn_ctr_Login_Login_DNN_txtPassword", password)
            page.click("#dnn_ctr_Login_Login_DNN_cmdLogin")
            page.wait_for_load_state("networkidle")
            
            page.goto("https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=180", timeout=60000)
            grid_selector = "#dnn_ctr546_Document_grdDocuments"
            page.wait_for_selector(grid_selector, timeout=45000)
            
            rows = page.locator(f"{grid_selector} tr").all()
            manifest = []

            for row in rows:
                dl_link = row.locator("a[id*='ctlDownloadLink']").first
                if dl_link.count() > 0:
                    try:
                        cells = row.locator("td").all()
                        title_raw = cells[1].inner_text().strip()
                        category = cells[2].inner_text().strip()
                        date_raw = cells[3].inner_text().strip()
                        
                        filename = clean_filename_v3(title_raw)
                        dest_path = download_dir / filename

                        if not dest_path.exists():
                            print(f"Harvesting: {filename}")
                            with page.expect_download(timeout=90000) as download_info:
                                dl_link.click()
                            download = download_info.value
                            download.save_as(str(dest_path))
                        
                        manifest.append({
                            "filename": filename,
                            "original_title": title_raw,
                            "category": category,
                            "date": date_raw,
                            "path": str(dest_path)
                        })
                    except Exception as e:
                        pass

            with open(metadata_dir / "hanhchinh_manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            print(f"Audit Complete. Cleaned and cataloged.")

        finally:
            browser.close()

if __name__ == "__main__":
    surgical_harvest_v3()
