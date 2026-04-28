"""
RabbitMQ Worker (Event-Driven Architecture)
---
Implements the EDA pattern from Phuong's system design.
- Collector publishes an "index_document" event after harvesting.
- This Worker listens 24/7 and triggers Vector DB indexing automatically.
"""
import json
import logging
import sys
from pathlib import Path

# Add parent paths
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR / "search-agent"))
sys.path.append(str(BASE_DIR / "collector_agent"))

from pdf_processor import PDFProcessor
from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mq-worker")

# --- Publisher: Called by Collector after harvesting ---
def publish_index_event(file_path: str, source_url: str):
    """
    Publish an 'index_document' event to the queue.
    (Uses pika if RabbitMQ is available, falls back to direct call for local dev.)
    """
    try:
        import pika
        params = pika.ConnectionParameters("localhost")
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue="index_queue", durable=True)
        msg = json.dumps({"file_path": file_path, "source_url": source_url})
        ch.basic_publish(
            exchange="",
            routing_key="index_queue",
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)  # Persistent
        )
        conn.close()
        log.info(f"[MQ] Published index event for: {file_path}")
    except ImportError:
        log.warning("[MQ] pika not installed. Falling back to direct indexing.")
        _direct_index(file_path, source_url)
    except Exception as e:
        log.error(f"[MQ] Failed to publish. Falling back. Error: {e}")
        _direct_index(file_path, source_url)


def _direct_index(file_path: str, source_url: str):
    """Fallback: index directly without MQ (for local development)."""
    log.info(f"[DIRECT] Indexing: {file_path}")
    processor = PDFProcessor()
    vdb = VectorDBClient()
    embedder = EmbeddingService()

    chunks = processor.extract_text_by_article(file_path)
    chunks = [c for c in chunks if len(c["content"].strip()) > 50]
    if not chunks:
        log.warning(f"[DIRECT] No valid chunks from {file_path}")
        return

    texts = [f"{c['title']} {c['content']}" for c in chunks]
    vectors = embedder.embed_texts(texts)
    vdb.upsert_chunks(chunks, vectors)
    log.info(f"[DIRECT] Indexed {len(chunks)} chunks from {Path(file_path).name}")


# --- Consumer: The always-on Worker ---
def start_worker():
    """Start the RabbitMQ consumer worker. Runs indefinitely."""
    log.info("[WORKER] Starting MQ Worker... Waiting for index events.")

    processor = PDFProcessor()
    vdb = VectorDBClient()
    embedder = EmbeddingService()

    def callback(ch, method, properties, body):
        try:
            event = json.loads(body)
            file_path = event.get("file_path")
            source_url = event.get("source_url", "")
            log.info(f"[WORKER] Received event for: {file_path}")

            chunks = processor.extract_text_by_article(file_path)
            chunks = [c for c in chunks if len(c["content"].strip()) > 50]
            if not chunks:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            texts = [f"{c['title']} {c['content']}" for c in chunks]
            vectors = embedder.embed_texts(texts)
            vdb.upsert_chunks(chunks, vectors)
            log.info(f"[WORKER] SUCCESS: Indexed {len(chunks)} chunks.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            log.error(f"[WORKER] Failed to process message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    try:
        import pika
        params = pika.ConnectionParameters("localhost")
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue="index_queue", durable=True)
        ch.basic_qos(prefetch_count=1)
        ch.basic_consume(queue="index_queue", on_message_callback=callback)
        ch.start_consuming()
    except ImportError:
        log.error("[WORKER] pika not installed. Run: pip install pika")
    except KeyboardInterrupt:
        log.info("[WORKER] Shutting down gracefully.")


if __name__ == "__main__":
    start_worker()
