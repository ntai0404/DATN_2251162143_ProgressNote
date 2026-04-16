import requests
import time
import json

def run_demo():
    BASE_URL = "http://localhost:8001"
    
    print("--- TLU Regulations AI Demo ---")
    
    # 1. Semantic Search Test
    query = "Quy chế đào tạo đại học là gì?"
    print(f"\nStep 1: User asks: '{query}'")
    
    try:
        response = requests.post(f"{BASE_URL}/search", json={"query": query, "top_k": 2})
        if response.status_code == 200:
            results = response.json()
            print(f"Step 2: Search Agent found {len(results)} relevant articles in Vector DB:")
            for i, res in enumerate(results):
                print(f"  [{i+1}] {res['title']}")
                print(f"      Source: {res['metadata']['source']}")
                # print(f"      Snippet: {res['content'][:150]}...")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection error: {e}. Please ensure Search API is running.")

if __name__ == "__main__":
    run_demo()
