import os
import sys

# Setup paths
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "search-agent"))
sys.path.append(os.path.join(current_dir, "shared"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

def test_direct():
    print("DIRECT SEARCH TEST (Bypassing API to check data integrity)")
    print("="*60)
    
    vdb = VectorDBClient()
    embedder = EmbeddingService()
    
    query = "Quy định về học bổng khuyến khích học tập Thủy Lợi"
    print(f"QUERY: {query}")
    
    query_vector = embedder.embed_texts(query)[0]
    hits = vdb.search(query_vector, limit=2)
    
    if not hits:
        print("RESULT: No data found in 'tlu_knowledge' collection.")
        return

    for i, hit in enumerate(hits):
        payload = hit.payload
        print(f"\n--- MATCH {i+1} (Score: {hit.score:.4f}) ---")
        print(f"TITLE: {payload.get('title')}")
        print(f"SOURCE: {payload.get('source')}")
        print(f"URL/PATH: {payload.get('url') or payload.get('source_url')}")
        print(f"CONTENT PREVIEW (First 500 chars):")
        print("-" * 20)
        content = payload.get('content', '')
        print(content[:500])
        print("-" * 20)
        
        # Check for encoding issues
        try:
            content.encode('utf-8')
            print("FORMATTING CHECK: UTF-8 Encoding Valid.")
        except UnicodeError:
            print("FORMATTING CHECK: ERROR - Encoding issues detected!")
            
        if "\n" in content:
            print("STRUCTURE CHECK: Newlines preserved.")
        else:
            print("STRUCTURE CHECK: WARNING - Newlines might be stripped.")

if __name__ == "__main__":
    test_direct()
