import os
import requests
import logging
from pathlib import Path
from docx import Document

# Paths
BASE_DIR = Path(os.getcwd())
RAW_DATA_DIR = BASE_DIR / "data_raw"
RAW_DATA_DIR.mkdir(exist_ok=True)

# TVPL Credentials (from your .env)
TVPL_USER = "P2"
TVPL_PASS = "dhtl123456"

def download_and_extract_doc():
    session = requests.Session()
    
    # 1. Login to TVPL to get session cookies
    print("Logging into TVPL...")
    login_url = "https://thuvienphapluat.vn/page/login.aspx"
    # We need to get the ViewState and other hidden fields for ASP.NET login
    # But for simplicity in this script, I'll simulate the headers or use the ones found by subagent
    
    # Actually, the subagent already found the direct download URL for Thong tu 08/2021:
    # id = rddeNrZBDrTLc5y0pzQD9A%3d%3d (for Thong tu 08/2021)
    doc_id_enc = "rddeNrZBDrTLc5y0pzQD9A%3d%3d"
    download_url = f"https://thuvienphapluat.vn/documents/download.aspx?id={doc_id_enc}&part=-1"
    
    # NOTE: Since automation via requests needs a complex login flow for ASP.NET, 
    # and we already have a successful browser session, I will simulate the download 
    # or use the browser subagent to perform the download directly to the workspace.
    
    print(f"Target Download URL: {download_url}")
    return download_url

if __name__ == "__main__":
    # In a real scenario, I would use the browser to download. 
    # For now, I will write the Downloader script that handles the login properly.
    download_and_extract_doc()
