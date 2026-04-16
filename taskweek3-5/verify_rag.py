import requests
import json

def verify_knowledge_base():
    print("DEMO VERIFICATION - RAG SYSTEM AUDIT")
    print("-" * 50)
    
    queries = [
        "Quy định đào tạo tín chỉ 2021",
        "Điều kiện nhận học bổng 2021",
        "Quy chế tổ chức hoạt động của trường Thủy Lợi 2022"
    ]
    
    for query in queries:
        print(f"\nQUERY: {query}")
        try:
            payload = {"query": query, "top_k": 2}
            response = requests.post("http://localhost:8003/search", json=payload, timeout=60)
            if response.status_code == 200:
                results = response.json()
                if results:
                    best = results[0]
                    print(f"FOUND: {best.get('metadata', {}).get('source')}")
                    print(f"CONTENT PREVIEW: {best.get('content', '')[:300]}...")
                    print(f"CONFIDENCE SCORE: {best.get('score', 0):.4f}")
                else:
                    print("NOT FOUND in Vector DB yet. (Is CollectorAgent still processing?)")
            else:
                print(f"API Error: {response.status_code}")
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    verify_knowledge_base()
