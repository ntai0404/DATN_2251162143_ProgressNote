import logging
import sys
from pathlib import Path
from collector_v3 import universal_collect

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("batch-harvester")

# 🎯 THE CIRCLE OF KNOWLEDGE - TARGET LIST
# This list maps to the hierarchy requested by the Mentor.
TARGET_URLS = [
    # --- RING 4: TLU Internal (Core) ---
    "https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=118", # Instructions
    "https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=180", # Regulations List
    "https://hanhchinh.tlu.edu.vn/Default.aspx?tabid=74",  # Weekly Calendar
    
    # --- RING 3: Higher Education Law ---
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Van-ban-hop-nhat-42-VBHN-VPQH-2018-Luat-Giao-duc-dai-hoc-405085.aspx",
    
    # --- RING 2: General Education Law ---
    "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-363406.aspx",
    
    # --- RING 1: Public Career Units & Personnel ---
    "https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Van-ban-hop-nhat-26-VBHN-VPQH-2020-Luat-Vien-chuc-448881.aspx",
    "https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Nghi-dinh-60-2021-ND-CP-co-che-tu-chu-tai-chinh-cua-don-vi-su-nghiep-cong-lap-449431.aspx"
]

def run_total_scan():
    log.info("=====================================================")
    log.info("🚀 STARTING TOTAL KNOWLEDGE SCAN (1-CLICK MODE)")
    log.info("=====================================================")
    
    success_count = 0
    fail_count = 0
    
    for i, url in enumerate(TARGET_URLS, 1):
        log.info(f"\n[SCAN {i}/{len(TARGET_URLS)}] Target: {url}")
        try:
            universal_collect(url)
            success_count += 1
        except Exception as e:
            log.error(f"Failed to harvest {url}: {e}")
            fail_count += 1
            
    log.info("\n" + "="*53)
    log.info(f"🏁 SCAN COMPLETED.")
    log.info(f"✅ Success: {success_count}")
    log.info(f"❌ Failed:  {fail_count}")
    log.info("Check 'collector_v7.log' for detailed deep-harvest logs.")
    log.info("="*53)

if __name__ == "__main__":
    run_total_scan()
