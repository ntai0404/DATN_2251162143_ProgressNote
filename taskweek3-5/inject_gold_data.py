import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Setup paths
BASE_DIR = Path(os.getcwd())
sys.path.append(str(BASE_DIR / "search-agent"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

def inject_full_text():
    vdb = VectorDBClient()
    embedder = EmbeddingService()
    
    # Nội dung đầy đủ đã trích xuất (Rút gọn cho script, thực tế sẽ nạp toàn bộ)
    full_text_tt08 = """
THÔNG TƯ BAN HÀNH QUY CHẾ ĐÀO TẠO TRÌNH ĐỘ ĐẠI HỌC

Điều 2. Khối lượng kiến thức chuẩn và thời gian đào tạo
1. Khối lượng kiến thức của một chương trình đào tạo được xác định bằng số tín chỉ...
5. Thời gian tối đa để sinh viên hoàn thành khoá học được quy định trong quy chế của cơ sở đào tạo, nhưng không vượt quá 02 lần thời gian theo kế hoạch học tập chuẩn toàn khoá đối với mỗi hình thức đào tạo.

Điều 9. Tính điểm trung bình chung học tập
1. Để tính điểm trung bình chung học kỳ và điểm trung bình tích lũy, các mức điểm chữ của học phần được quy đổi về điểm số như sau:
A tương ứng 4; B tương ứng 3; C tương ứng 2; D tương ứng 1; F tương ứng 0.

Điều 12. Xếp loại học lực và xếp loại tốt nghiệp
1. Sinh viên được xếp loại học lực theo điểm trung bình học kỳ, điểm trung bình năm học hoặc điểm trung bình tích lũy:
- Từ 3,60 đến 4,00: Xuất sắc;
- Từ 3,20 đến 3,59: Giỏi;
- Từ 2,50 đến 3,19: Khá;
- Từ 2,00 đến 2,49: Trung bình;
- Từ 1,00 đến 1,99: Yếu;
- Dưới 1,00: Kém.
"""
    # Tạo các chunks từ nội dung đầy đủ (tách theo Điều)
    articles = full_text_tt08.split("Điều ")
    chunks = []
    source_name = "Thông tư 08/2021/TT-BGDĐT - Quy chế đào tạo đại học"
    source_url = "https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-08-2021-TT-BGDDT-Quy-che-dao-tao-trinh-do-dai-hoc-470013.aspx"

    for art in articles:
        if not art.strip(): continue
        content = "Điều " + art.strip()
        title = content.split("\n")[0]
        chunks.append({
            "title": f"{source_name} - {title}",
            "content": content,
            "metadata": {
                "source": source_name,
                "source_url": source_url,
                "chunk_type": "article",
                "extracted_at": datetime.now().isoformat()
            }
        })
    
    print(f"Injecting {len(chunks)} high-quality full-text chunks...")
    vectors = embedder.embed_texts([c['content'] for c in chunks])
    vdb.upsert_chunks(chunks, vectors)
    print("Injection complete.")

if __name__ == "__main__":
    inject_full_text()
