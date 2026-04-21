import os
import sys
from datetime import datetime

# Setup paths
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "search-agent"))

from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService
from qdrant_client.http import models

def test_full_text_only():
    vdb = VectorDBClient()
    embedder = EmbeddingService()
    
    query = "Thời gian thực hiện chương trình đào tạo đại học"
    print(f"Searching specifically for FULL TEXT content for: '{query}'...")
    
    vector = embedder.embed_texts([query])[0]
    
    # Sử dụng query_points cho version mới, hoặc search cho version cũ
    try:
        # Thử phương thức query_points (version 1.10+)
        search_result = vdb.client.query_points(
            collection_name=vdb.collection_name,
            query=vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="chunk_type",
                        match=models.MatchValue(value="article")
                    )
                ]
            ),
            limit=3
        )
        results = search_result.points
    except Exception as e:
        print(f"query_points failed: {e}. Trying legacy search...")
        results = vdb.client.search(
            collection_name=vdb.collection_name,
            query_vector=vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="chunk_type",
                        match=models.MatchValue(value="article")
                    )
                ]
            ),
            limit=3
        )
    
    report = []
    report.append("# EVIDANCE: FULL TEXT CONTENT RETRIEVAL (Actual Data Proof)")
    report.append(f"**Query:** {query}")
    report.append("**Timestamp:** " + datetime.now().isoformat())
    report.append("\n" + "="*80 + "\n")
    
    if not results:
        report.append("❌ NO FULL TEXT (article) FOUND. Most results in DB are currently 'metadata_index'.")
        report.append("\n**Checking what IS in the DB:**")
        scroll = vdb.client.scroll(collection_name=vdb.collection_name, limit=5)[0]
        for p in scroll:
            report.append(f"- Type: {p.payload.get('chunk_type')} | Title: {p.payload.get('title')[:50]}")
    else:
        for idx, res in enumerate(results):
            payload = res.payload
            score = res.score
            
            content = payload.get('content', '')
            source = payload.get('source', 'Unknown')
            report.append(f"### [FULL TEXT RESULT {idx+1}]")
            report.append(f"**Source:** {source}")
            report.append(f"**Score:** {score:.4f}")
            report.append("**Actual Text Content (Full Content):**")
            report.append(f"\n```text\n{content}\n```\n")
            report.append("-" * 30)

    with open("EVIDENCE_FULL_TEXT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("Evidence file created: EVIDENCE_FULL_TEXT.md")

if __name__ == "__main__":
    test_full_text_only()
