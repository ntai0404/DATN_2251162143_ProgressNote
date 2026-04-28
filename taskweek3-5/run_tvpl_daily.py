"""
run_tvpl_daily.py
==================
Điểm kích hoạt cào và nạp dữ liệu TVPL hàng ngày.

Nhiệm vụ:
1. Cào 7 văn bản ưu tiên (nếu có cập nhật hoặc chưa có).
2. Tự động mở rộng hàng chờ (Discovery Phase) thêm N văn bản.
3. Tự động nạp (Ingest) các văn bản mới vào Qdrant Vector DB.

Cách dùng:
    python run_tvpl_daily.py --discover 10
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from collector_agent.core.orchestrator import CollectorOrchestrator

def main():
    parser = argparse.ArgumentParser(description="TVPL Daily Harvester & Ingestor")
    parser.add_argument("--discover", type=int, default=10, 
                        help="Số lượng văn bản mới muốn mở rộng thêm. Mặc định=10. Dùng -1 để cào toàn bộ (Unlimited).")
    parser.add_argument("--debug", action="store_true", 
                        help="Hiện trình duyệt khi cào.")
    
    args = parser.parse_args()
    max_disc = None if args.discover == -1 else args.discover

    # Đảm bảo thư mục logs tồn tại
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Cấu hình logging chuẩn Microservice (RotatingFileHandler chống tràn ổ cứng)
    from logging.handlers import RotatingFileHandler
    log_format = logging.Formatter("%(asctime)s | %(name)-22s | [%(levelname)s] | %(message)s")
    
    file_handler = RotatingFileHandler(
        log_dir / "tvpl_collector.log", 
        maxBytes=5*1024*1024, # 5MB mỗi file
        backupCount=3,        # Lưu tối đa 3 file cũ
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_format)

    # Gắn vào root logger để gom log của TOÀN BỘ các file con (spider, browser, qdrant...)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Tránh gắn duplicate handler nếu chạy lại
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
    
    log = logging.getLogger("System.DailyRun")
    log.info("="*60)
    log.info("BẮT ĐẦU TIẾN TRÌNH CÀO DỮ LIỆU TVPL HÀNG NGÀY")
    log.info(f"Cấu hình: discover={max_disc}, debug={args.debug}")
    log.info("="*60)

    try:
        orchestrator = CollectorOrchestrator()
        
        # Nếu muốn hiện trình duyệt, cần chỉnh sửa tạm thời headless mode của harvester
        # Ở đây ta dùng mặc định headless=True trong orchestrator.py
        
        total_chunks = orchestrator.run_tvpl_pipeline(
            max_discovery=max_disc, 
            headless=not args.debug
        )
        
        log.info("="*60)
        log.info(f"HOÀN THÀNH: Đã nạp thêm {total_chunks} blocks kiến thức vào Qdrant.")
        log.info("="*60)
        
    except Exception as e:
        log.error(f"LỖI TIẾN TRÌNH: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
