import os
import sys
import json
import requests
import time
from datetime import datetime
from pathlib import Path

# Setup paths
BASE_DIR = Path(os.getcwd())

# Fix terminal encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def run_test():
    query = "Nội dung nội quy nội trú có những gì?"
    API_URL = "http://localhost:8003/search"
    
    print(f"Testing Query: {query}")
    
    report = []
    report.append("# BÁO CÁO THỬ NGHIỆM TRUY VẤN RAG (QA Summary)")
    report.append(f"- **Ngày chạy:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"- **Câu hỏi test:** `{query}`")
    report.append("\n" + "="*50 + "\n")
    
    try:
        # Wait for API
        print("Waiting for Search API to be ready...")
        for _ in range(30):
            try:
                if requests.get("http://localhost:8003/").status_code == 200:
                    break
            except:
                pass
            time.sleep(2)
        else:
            report.append("❌ **Lỗi:** Search API không phản hồi sau 60s.")
            save_report(report)
            return

        # 1. Trigger Refresh
        print("Refreshing Index...")
        requests.post("http://localhost:8003/refresh")
        
        # 2. Search
        print(f"Sending query: {query}")
        resp = requests.post(API_URL, json={"query": query, "top_k": 5})
        if resp.status_code == 200:
            results = resp.json()
            if not results:
                report.append("❌ **Kết quả:** Không tìm thấy dữ liệu.")
            else:
                report.append(f"✅ **Tìm thấy:** {len(results)} kết quả.\n")
                
                # Check if correct document was found
                found_target = False
                target_results = []
                
                for i, res in enumerate(results):
                    title = res.get('title', '')
                    content = res.get('content', '')
                    score = res.get('score', 0)
                    metadata = res.get('metadata', {})
                    
                    report.append(f"### Kết quả {i+1} (Score: {score:.4f})")
                    report.append(f"- **Tiêu đề:** {title}")
                    report.append(f"- **Nguồn file:** {metadata.get('source_file', 'N/A')}")
                    report.append(f"- **Nội dung trích xuất:**\n\n```text\n{content[:1000]}...\n```\n")
                    
                    if "Nội quy khu Nội trú" in title or "Nội trú" in title:
                        found_target = True
                        target_results.append(res)
                
                report.append("\n" + "="*50 + "\n")
                report.append("## 📝 ĐÁNH GIÁ CHẤT LƯỢNG")
                
                if found_target:
                    report.append("- **Độ chính xác tài liệu:** ✅ Đạt (Tìm thấy đúng tài liệu về Nội quy nội trú).")
                else:
                    report.append("- **Độ chính xác tài liệu:** ❌ Không đạt (Không tìm thấy tài liệu Nội quy nội trú trong Top 5).")
                
                # Check for completeness
                total_chars = sum(len(r.get('content', '')) for r in target_results)
                if total_chars > 2000:
                    report.append("- **Độ đầy đủ:** ✅ Tốt (Lấy được diện rộng các Điều/Khoản, tổng cộng khoảng " + str(total_chars) + " ký tự).")
                elif total_chars > 0:
                    report.append("- **Độ đầy đủ:** ⚠️ Cảnh báo (Chỉ lấy được một mảnh/vài Điều - " + str(total_chars) + " ký tự. Có thể chưa bao quát hết toàn bộ nội quy).")
                else:
                    report.append("- **Độ đầy đủ:** ❌ Không có dữ liệu nội dung.")
                    
                report.append("- **Kết luận:** Hệ thống " + ("CÓ" if found_target else "KHÔNG") + " lấy được nội dung từ file MD trong ocr_diagnostics.")
        else:
            report.append(f"❌ **Lỗi API:** Code {resp.status_code} - {resp.text}")
    except Exception as e:
        report.append(f"❌ **Lỗi hệ thống:** {str(e)}")

    save_report(report)
    print("Test complete. Results saved in QA_summary.md")

def save_report(report):
    with open("QA_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))

if __name__ == "__main__":
    run_test()
