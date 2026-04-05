import requests
from bs4 import BeautifulSoup
import re
import os
import hashlib
from urllib.parse import urljoin, urlparse

# TLU Regulation Discovery Agent Prototype
# This script demonstrates dynamic link discovery (Link Động) instead of static hardcoding.

class DynamicCollectorAgent:
    def __init__(self, seed_urls, data_dir="taskWeek1-2/data_raw"):
        self.seed_urls = seed_urls
        self.data_dir = data_dir
        self.visited = set()
        self.downloaded_hashes = set()
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def is_tlu_domain(self, url):
        return "tlu.edu.vn" in urlparse(url).netloc

    def get_file_hash(self, content):
        return hashlib.md5(content).hexdigest()

    def discover_and_collect(self, url, depth=1):
        if depth < 0 or url in self.visited:
            return
        
        self.visited.add(url)
        print(f"[*] Agent searching at: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Find and download PDFs dynamically
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Filter for Regulation/Announcement PDF links
                if full_url.endswith('.pdf') and any(kw in full_url.lower() for kw in ['quy-che', 'quy-dinh', 'thong-bao', 'văn-bản']):
                    self.download_pdf(full_url)
                
                # 2. Recursive Search (Dynamic Endpoint Linking)
                elif self.is_tlu_domain(full_url) and depth > 0:
                    self.discover_and_collect(full_url, depth - 1)
                    
        except Exception as e:
            print(f"[!] Error at {url}: {e}")

    def download_pdf(self, url):
        try:
            response = requests.get(url, stream=True)
            content = response.content
            file_hash = self.get_file_hash(content)
            
            if file_hash in self.downloaded_hashes:
                return
                
            filename = os.path.basename(urlparse(url).path)
            filepath = os.path.join(self.data_dir, f"{file_hash[:8]}_{filename}")
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            self.downloaded_hashes.add(file_hash)
            print(f"[+] Agent Collected: {url} -> {filepath}")
            
        except Exception as e:
            print(f"[!] Download Failed {url}: {e}")

if __name__ == "__main__":
    seeds = [
        "https://www.tlu.edu.vn/dao-tao/dai-hoc-chinh-quy-10173",
        "https://daotao.tlu.edu.vn/",
        "https://ctsv.tlu.edu.vn/"
    ]
    agent = DynamicCollectorAgent(seeds)
    print("=== TLU Collector Agent Running (Discovery Mode) ===")
    for seed in seeds:
        agent.discover_and_collect(seed, depth=1)
