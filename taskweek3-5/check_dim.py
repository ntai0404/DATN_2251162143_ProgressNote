import sys
import os
sys.path.append(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\search-agent")
from embedding_service import EmbeddingService
s = EmbeddingService()
print(f"DIM: {len(s.embed_texts('test')[0])}")
