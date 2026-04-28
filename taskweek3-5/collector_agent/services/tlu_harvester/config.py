import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm thư mục gốc (taskweek3-5)
_BASE_DIR = Path(__file__).resolve().parents[3]

# Load env từ thư mục gốc và collector_agent
load_dotenv(_BASE_DIR / ".env")
load_dotenv(_BASE_DIR / "collector_agent" / ".env")

# Credentials
TLU_USER = os.getenv("HANH_CHINH_TLU_USER", "dxdung")
TLU_PASS = os.getenv("HANH_CHINH_TLU_PASS", "Dolinhdan2014")

# URLs
TLU_PORTAL = "https://hanhchinh.tlu.edu.vn"
DEFAULT_TABS = [
    f"{TLU_PORTAL}/Default.aspx?tabid=74",  # Văn bản quy định
    f"{TLU_PORTAL}/Default.aspx?tabid=180", # Công văn
]

# Browser Config
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
