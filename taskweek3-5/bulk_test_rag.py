import requests
import json
import time
import sys

# Windows console encoding fix
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Base URL for Search API
SEARCH_URL = "http://localhost:8003/search"

# List of 20 test queries covering various categories
TEST_QUERIES = [
    "Quy định xét cấp học bổng khuyến khích học tập",
    "Quy chế đào tạo trình độ đại học mới nhất 2025",
    "Mức trích nộp kinh phí của các đơn vị chuyên môn",
    "Nội quy phòng thí nghiệm kỹ thuật hóa học",
    "Quy định về chuẩn đầu ra ngoại ngữ và miễn học",
    "Chế độ phụ cấp lương cho giảng viên nhóm ngành cao",
    "Quy định lấy ý kiến người học về hoạt động giảng dạy",
    "Nội quy tiếp công dân của trường Đại học Thủy lợi",
    "Quy chế chi tiêu nội bộ của trường năm 2021",
    "Quy định về thi Olympic môn học và miễn thi",
    "Điều kiện làm đồ án tốt nghiệp khoa Kinh tế 2020",
    "Quy định quản lý sử dụng thiết bị vật tư điện nước",
    "Quy trình khảo sát cựu sinh viên và việc làm",
    "Quy chế hoạt động hợp tác quốc tế của trường",
    "Nội quy khu nội trú sinh viên Đại học Thủy lợi",
    "Quy định về đánh giá kết quả rèn luyện sinh viên",
    "Điều lệ tổ chức và hoạt động của trường TLU 2022",
    "Quy định về tổ chức thi trực tuyến tại trường",
    "Quy định quản lý ô tô ra vào khuôn viên trường",
    "Quy định kéo dài thời gian làm việc và hưu trí"
]

def run_bulk_test():
    print(f"{'#'*60}")
    print(f"{'BULK RAG TEST - 20 QUERIES':^60}")
    print(f"{'#'*60}\n")
    
    audit_results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/20] Testing: {query}...")
        try:
            payload = {"query": query, "top_k": 1}
            start_time = time.time()
            response = requests.post(SEARCH_URL, json=payload, timeout=20)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    top_hit = results[0]
                    audit_results.append({
                        "id": i,
                        "query": query,
                        "found": True,
                        "title": top_hit.get("title"),
                        "score": top_hit.get("score"),
                        "snippet": top_hit.get("content")[:150],
                        "latency": latency
                    })
                else:
                    audit_results.append({"id": i, "query": query, "found": False, "error": "No results"})
            else:
                audit_results.append({"id": i, "query": query, "found": False, "error": f"HTTP {response.status_code}"})
                
        except Exception as e:
            audit_results.append({"id": i, "query": query, "found": False, "error": str(e)})
        
        time.sleep(0.5) # Prevent overloading
        
    # Summarize to JSON for report processing
    with open("rag_test_results.json", "w", encoding='utf-8') as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)
    
    print(f"\nTest complete. Results saved to rag_test_results.json")

if __name__ == "__main__":
    run_bulk_test()
