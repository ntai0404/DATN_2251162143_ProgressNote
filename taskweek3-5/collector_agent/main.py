import os
import json
import logging
import time
import hashlib
import sys

# PROGRAMMATIC PATH RESOLUTION FOR DEMO COHESION
# We add the root directory and the search-agent/shared directories explicitly
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(current_dir)
sys.path.append(root_path)
sys.path.append(os.path.join(root_path, "search-agent"))
sys.path.append(os.path.join(root_path, "shared"))

# Import locally to avoid package naming issues
from pdf_processor import PDFProcessor
from web_scraper import WebScraper
import pika
from vector_db_client import VectorDBClient
from embedding_service import EmbeddingService

from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, ".env"))

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('collector-agent')

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

class CollectorAgent:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.web_scraper = WebScraper()
        self.vdb_client = VectorDBClient()
        self.embedding_service = EmbeddingService()
        self.setup_mq()

    def setup_mq(self):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='collector_tasks', durable=True)
            self.channel.queue_declare(queue='crawled_data', durable=True)
            logger.info("RabbitMQ setup complete.")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    def save_raw_data(self, data):
        try:
            uid = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
            target_dir = os.path.join(root_path, "data_scraped")
            os.makedirs(target_dir, exist_ok=True)
            filepath = os.path.join(target_dir, f"{uid}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved raw data to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")

    def publish_data(self, data):
        try:
            message = json.dumps(data)
            self.channel.basic_publish(
                exchange='',
                routing_key='crawled_data',
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"Published data for: {data.get('title')}")
        except Exception as e:
            logger.error(f"Failed to publish data: {e}")

    def process_task(self, ch, method, properties, body):
        task = json.loads(body)
        url = task.get('url')
        task_type = task.get('type') 
        name = task.get('name', 'Unknown')
        
        logger.info(f"Processing task: {task_type} - {name} ({url})")
        
        results = []
        try:
            if task_type in ['pdf', 'process_pdf']:
                target = task.get('path') or url
                if target:
                    results = self.pdf_processor.extract_text_by_article(target)
                else:
                    logger.error("No path or url provided for PDF task")
            elif task_type == 'web':
                if url:
                    results = self.web_scraper.scrape_tlu_news(url)
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            
        for result in results:
            self.save_raw_data(result)
            self.publish_data(result)
            
            # DIRECT UPSERT
            try:
                vectors = self.embedding_service.embed_texts([result['content']])
                self.vdb_client.upsert_chunks([result], vectors)
                logger.info(f"Direct Upsert Successful for: {result.get('title')}")
            except Exception as e:
                logger.error(f"Direct Upsert Failed: {e}")
            
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='collector_tasks', on_message_callback=self.process_task)
        logger.info("Collector Agent is waiting for tasks...")
        self.channel.start_consuming()

if __name__ == "__main__":
    agent = CollectorAgent()
    agent.start_consuming()
