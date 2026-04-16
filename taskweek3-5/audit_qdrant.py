import requests
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models

def audit_qdrant():
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "tlu_regulations"
    
    print(f"AUDITING COLLECTION: {collection_name}")
    try:
        count = client.get_collection(collection_name).points_count
        print(f"TOTAL POINTS: {count}")
        
        # Get one sample point
        points = client.scroll(collection_name=collection_name, limit=1)[0]
        if points:
            print("SAMPLE POINT FOUND:")
            print(json.dumps(points[0].payload, indent=2, ensure_ascii=False))
        else:
            print("NO POINTS FOUND - CollectorAgent might still be processing.")
            
    except Exception as e:
        print(f"Qdrant Error: {e}")

if __name__ == "__main__":
    audit_qdrant()
