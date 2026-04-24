import numpy as np
from rank_bm25 import BM25Okapi
import re

class HybridSearchEngine:
    def __init__(self, dense_embedder):
        self.dense_embedder = dense_embedder
        self.bm25 = None
        self.chunks = []
        self.chunk_vectors = []

    def fit(self, chunks):
        """Nạp dữ liệu và huấn luyện bộ chỉ mục BM25"""
        self.chunks = chunks
        
        # Chuẩn bị dữ liệu cho BM25 (Tokenize đơn giản)
        tokenized_corpus = [self._tokenize(c['content']) for c in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        # Chuẩn bị dữ liệu cho Dense Vector
        self.chunk_vectors = self.dense_embedder.embed_texts([c['content'] for c in chunks])
        print(f"[HybridSearch] Indexing complete: {len(chunks)} chunks.")

    def _tokenize(self, text):
        return re.sub(r'[^\w\s]', '', text.lower()).split()

    def search(self, query, top_k=3):
        """Thực thi Hybrid Search với cơ chế Vote (RRF)"""
        # 1. Dense Search Score (Cosine Similarity)
        query_vector = self.dense_embedder.embed_texts([query])[0]
        dense_scores = [self._cosine_similarity(query_vector, cv) for cv in self.chunk_vectors]
        
        # 2. BM25 Search Score
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # 3. Kết hợp kết quả (Reciprocal Rank Fusion - RRF)
        # Sắp xếp thứ hạng của từng bên
        dense_rank = np.argsort(np.argsort(dense_scores)[::-1])
        bm25_rank = np.argsort(np.argsort(bm25_scores)[::-1])
        
        hybrid_scores = []
        k = 60 # Hằng số RRF tiêu chuẩn
        for i in range(len(self.chunks)):
            # Tính điểm Vote: Càng đứng top ở cả 2 bên thì điểm càng cao
            score = (1.0 / (k + dense_rank[i])) + (1.0 / (k + bm25_rank[i]))
            hybrid_scores.append(score)
            
        # Lấy Top K kết quả cuối cùng
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "chunk": self.chunks[idx],
                "score": hybrid_scores[idx],
                "dense_score": dense_scores[idx],
                "bm25_score": bm25_scores[idx]
            })
        return results

    def _cosine_similarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
