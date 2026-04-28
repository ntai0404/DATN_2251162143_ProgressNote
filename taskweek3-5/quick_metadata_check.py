import sys
from pathlib import Path
import logging

# Add root to sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from collector_agent.services.tvpl_harvester.browser import TVPLBrowser
from collector_agent.services.tvpl_harvester.extractor import extract_page, build_markdown

logging.basicConfig(level=logging.INFO)

def quick_check():
    url = "https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-367665.aspx"
    with TVPLBrowser(headless=True) as ctx:
        page = ctx.new_page()
        result = extract_page(page, url)
        if result:
            md = build_markdown(result, url)
            print("\n" + "="*50)
            print("METADATA EXTRACTED:")
            print(md.split("\n\n")[0]) # Print only frontmatter and title
            print("="*50)
        else:
            print("Extraction failed!")

if __name__ == "__main__":
    quick_check()
