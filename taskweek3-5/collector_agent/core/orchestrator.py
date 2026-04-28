"""
collector_agent/core/orchestrator.py
=====================================
CollectorOrchestrator — điều phối toàn bộ pipeline thu thập dữ liệu.

Pipeline:
  1. TVPLHarvester.run()  →  Markdown files (output_dir)
  2. ContentProcessor     →  Semantic chunks
  3. EmbedModel           →  Vectors
  4. VectorService        →  Upsert vào Qdrant

Cách dùng đơn giản nhất:
    orchestrator = CollectorOrchestrator()
    orchestrator.run_tvpl_pipeline()              # chỉ 7 priority
    orchestrator.run_tvpl_pipeline(max_discovery=20)  # + discovery
    orchestrator.run_ingestion_pipeline(md_path)  # nạp file MD thủ công
"""

import uuid
import logging
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client.http import models

from ..services.ocr_service import ChandraOCRService
from ..services.vector_service import VectorService
from ..services.tvpl_harvester import TVPLHarvester
from ..processors.content_processor import ContentProcessor

log = logging.getLogger("Collector.Orchestrator")

# ── Paths mặc định ──────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parents[2]   # taskweek3-5/
TVPL_OUTPUT_DIR = _BASE_DIR / "data_raw" / "tvpl"
TVPL_STATE_FILE = _BASE_DIR / "data_raw" / "tvpl_spider_state.json"


class CollectorOrchestrator:
    def __init__(self):
        self.ocr_service   = ChandraOCRService()
        self.vector_service = VectorService()
        self.processor     = ContentProcessor()
        self.embed_model   = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # ── Public API ────────────────────────────────────────────────────────────

    def run_tvpl_pipeline(self, max_discovery: int | None = 0, headless: bool = True) -> int:
        """
        Thu thập văn bản từ TVPL rồi nạp ngay vào Qdrant.

        Args:
            max_discovery: Số văn bản mở rộng thêm (0 = chỉ 7 priority, None = vô hạn).
            headless: Hiện trình duyệt hay không.

        Returns:
            Số chunks đã upsert vào Qdrant.
        """
        log.info(f"Starting TVPL Pipeline (max_discovery={max_discovery}, headless={headless})")
        TVPL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Bước 1: Thu thập → Markdown files
        harvester = TVPLHarvester(
            output_dir=TVPL_OUTPUT_DIR,
            state_file=TVPL_STATE_FILE,
            headless=headless,
        )
        new_files = harvester.run(max_discovery=max_discovery)
        log.info(f"Harvested {len(new_files)} new files.")

        # Bước 2: Nạp từng file vào Qdrant
        total_chunks = 0
        for md_path in new_files:
            chunks = self.run_ingestion_pipeline(str(md_path))
            total_chunks += chunks

        log.info(f"TVPL Pipeline done. Total chunks upserted: {total_chunks}")
        return total_chunks

    def run_ingestion_pipeline(self, md_file_path: str) -> int:
        """
        Nạp một file Markdown đã có sẵn vào Qdrant.
        Hỗ trợ YAML frontmatter — metadata được lưu vào payload Qdrant.

        Returns:
            Số chunks đã upsert.
        """
        log.info(f"Ingesting: {md_file_path}")
        content = Path(md_file_path).read_text(encoding="utf-8")

        # Parse frontmatter nếu có
        doc_meta = _parse_frontmatter(content)

        chunks = self.processor.parse_high_fidelity_md(content)
        log.info(f"  {len(chunks)} chunks extracted.")

        self.vector_service.ensure_collection(vector_size=384)

        points, total = [], 0
        for i, chunk in enumerate(chunks):
            clean_text = self.processor.clean_text_for_embedding(chunk["text"])
            vector = self.embed_model.encode(clean_text).tolist()

            payload = chunk["metadata"]
            payload["text"]         = chunk["text"]
            payload["raw_content"]  = chunk.get("raw_html", chunk["text"])
            payload["source_file"]  = Path(md_file_path).name
            # Gắn thêm legal metadata vào payload để Search Agent có thể filter
            payload.update(doc_meta)

            points.append(
                models.PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
            )

            if len(points) >= 50:
                self.vector_service.upsert_points(points)
                log.info(f"    Upserted {i+1}/{len(chunks)} ...")
                points = []

        if points:
            self.vector_service.upsert_points(points)

        total = len(chunks)
        log.info(f"  Ingestion complete: {total} chunks.")
        return total


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_frontmatter(content: str) -> dict:
    """Trích YAML frontmatter (---..---) thành dict."""
    import re
    meta = {}
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        for line in match.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"')
    return meta
