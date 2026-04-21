import os
import sys
import json

# Setup paths
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "search-agent"))
sys.path.append(os.path.join(current_dir, "shared"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

def fix_system():
    print("Fixing System: Re-aligning Vector DB with 384-dim Embedding Model")
    vdb = VectorDBClient()
    embedder = EmbeddingService()
    
    # Re-init collection (wipes old one)
    print(f"Initializing collection '{vdb.collection_name}' with 384 dimensions...")
    vdb.init_collection(vector_size=384)
    
    scraped_dir = os.path.join(current_dir, "data_scraped")
    if not os.path.exists(scraped_dir):
        print(f"Error: {scraped_dir} not found.")
        return

    files = [f for f in os.listdir(scraped_dir) if f.endswith(".json")]
    print(f"Found {len(files)} items to re-ingest.")
    
    for filename in files:
        filepath = os.path.join(scraped_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                content = data.get('content', '')
                title = data.get('title', 'Unknown')
                metadata = data.get('metadata', {})
                
                # Check structure
                if not content:
                    continue
                
                print(f"Ingesting: {title[:50]}...")
                
                # Use current embedding service
                vectors = embedder.embed_texts([content])
                
                # Re-upsert
                vdb.upsert_chunks([data], vectors)
            except Exception as e:
                print(f"Failed to ingest {filename}: {e}")

    print("FIX COMPLETE. Vector DB is now aligned.")

if __name__ == "__main__":
    fix_system()
