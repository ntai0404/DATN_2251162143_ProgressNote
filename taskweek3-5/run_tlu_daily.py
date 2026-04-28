"""
run_tlu_daily.py
==================
Điểm kích hoạt thu thập văn bản từ Portal Hành chính TLU.

Nhiệm vụ:
1. Đăng nhập vào hanhchinh.tlu.edu.vn.
2. Quét các trang danh mục văn bản (Văn bản quy định, Công văn).
3. Tải các file PDF/DOC về thư mục data_raw/hanhchinh.

Cách dùng:
    python run_tlu_daily.py --pages 2
"""

import sys
import argparse
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from collector_agent.core.orchestrator import CollectorOrchestrator

def main():
    parser = argparse.ArgumentParser(description="TLU Administrative Harvester")
    parser.add_argument("--pages", type=int, default=1, 
                        help="Số lượng trang muốn quét trên mỗi danh mục. Mặc định=1. Dùng -1 để cào toàn bộ.")
    parser.add_argument("--debug", action="store_true", 
                        help="Hiện trình duyệt khi thu thập.")
    
    args = parser.parse_args()
    max_pages = None if args.pages == -1 else args.pages

    # Đảm bảo thư mục logs tồn tại
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Cấu hình logging
    log_format = logging.Formatter("%(asctime)s | %(name)-22s | [%(levelname)s] | %(message)s")
    
    file_handler = RotatingFileHandler(
        log_dir / "tlu_collector.log", 
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
    
    log = logging.getLogger("System.TLURun")
    log.info("="*60)
    log.info("BẮT ĐẦU THU THẬP VĂN BẢN HÀNH CHÍNH TLU")
    log.info(f"Cấu hình: pages={args.pages}, debug={args.debug}")
    log.info("="*60)

    try:
        orchestrator = CollectorOrchestrator()
        
        downloaded_files = orchestrator.run_tlu_pipeline(
            max_pages=max_pages, 
            headless=not args.debug
        )
        
        try:
            log.info("="*60)
            log.info(f"HOÀN THÀNH: Đã tải {len(downloaded_files)} file về data_raw/hanhchinh.")
            log.info("="*60)
        except UnicodeEncodeError:
            # Fallback cho terminal không hỗ trợ Unicode
            print(f"\nCOMPLETED: Downloaded {len(downloaded_files)} files to data_raw/hanhchinh.")
        
    except Exception as e:
        log.error(f"LỖI TIẾN TRÌNH: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
