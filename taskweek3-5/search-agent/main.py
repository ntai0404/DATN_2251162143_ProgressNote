import os
import json
import logging
import pika
from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService
from dotenv import load_dotenv

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('search-agent')

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

class SearchAgent:
    def __init__(self):
        self.vdb_client = VectorDBClient()
        self.embedding_service = EmbeddingService()
        self.setup_mq()
        # Initialize collection
        self.vdb_client.init_collection()

    def setup_mq(self):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='crawled_data', durable=True)
            logger.info("RabbitMQ setup complete.")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    def process_crawled_data(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            logger.info(f"Ingesting data: {data.get('title')}")
            
            # Content could be a string or a list of chunks
            content = data.get('content', '')
            if isinstance(content, str):
                chunks = [{"title": data.get('title'), "content": content, "metadata": data.get('metadata', {})}]
            else:
                chunks = content # Already chunked by PDF processor

            texts = [c["content"] for c in chunks]
            vectors = self.embedding_service.embed_texts(texts)
            
            self.vdb_client.upsert_chunks(chunks, vectors)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error ingesting data: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='crawled_data', on_message_callback=self.process_crawled_data)
        logger.info("Search Agent is waiting for crawled data...")
        self.channel.start_consuming()

if __name__ == "__main__":
    agent = SearchAgent()
    agent.start_consuming()
    print("Search Agent initialized.")
