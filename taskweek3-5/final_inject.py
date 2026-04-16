import os
import json
import uuid
import sys

# Add paths
sys.path.append(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\shared")
sys.path.append(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\search-agent")

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

def final_push():
    client = VectorDBClient()
    embedder = EmbeddingService()
    scraped_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_scraped"
    
    count = 0
    for filename in os.listdir(scraped_dir):
        if filename.endswith(".json"):
            with open(os.path.join(scraped_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                content = data.get('content', '')
                title = data.get('title', 'Unknown News')
                
                # Filter out 404/Menu garbage
                if "404" in content or "Skip to content" in content[:20]:
                    continue
                
                print(f"Injecting: {title}")
                chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
                client.upsert_chunks(chunks, {
                    "source": title,
                    "type": "tlu_news_2026",
                    "level": 5
                })
                count += 1
    
    print(f"--- SUCCESS ---")
    print(f"Total News Items Injected: {count}")

if __name__ == "__main__":
    final_push()
