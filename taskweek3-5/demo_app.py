import requests
import json
import sys

def run_demo():
    print("="*60)
    print("Demo App is running at http://localhost:3001")
    print("      TLU REGULATIONS AI - RAG DEMO APP (Week 3-5)")
    print("="*60)
    print("Hệ thống đã nạp 121 bản quy chế từ HCTLU và Luật TVPL.\n")
    
    while True:
        query = input("\n[Demo] Nhập câu hỏi (hoặc 'exit' để thoát): ")
        if query.lower() == 'exit':
            break
            
        print(f"\n[AI] Đang tìm kiếm trong kho dữ liệu văn bản pháp quy...\n")
        
        try:
            # Call our Search API on Port 8001 with POST
            payload = {"query": query, "top_k": 3}
            response = requests.post("http://localhost:8003/search", json=payload, timeout=60)
            if response.status_code == 200:
                results = response.json()
                
                if not results:
                    print("AI: Xin lỗi, em không tìm thấy quy định nào liên quan đến câu hỏi này.")
                else:
                    for i, res in enumerate(results[:3]): # Show top 3 results
                        source = res.get('metadata', {}).get('source', 'Unknown File')
                        content = res.get('content', '')
                        score = res.get('score', 0)
                        
                        print(f"--- TRÍCH DẪN {i+1} (Độ tin cậy: {score:.2f}) ---")
                        print(f"NGUỒN: {source}")
                        print(f"NỘI DUNG:")
                        # Truncate content for cleaner demo if too long
                        if len(content) > 1000:
                            print(content[:1000] + "...")
                        else:
                            print(content)
                        print("-" * 40)
            else:
                print(f"Lỗi: Không thể kết nối tới Search API (Code {response.status_code})")
        except Exception as e:
            print(f"Lỗi hệ thống: {e}")
            print("Đảm bảo python search-agent/search_api.py đang chạy tại port 8000.")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    run_demo()
