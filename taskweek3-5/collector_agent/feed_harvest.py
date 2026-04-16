import pika
import json
import os
import sys

# Send messages for all PDFs in data_raw
def feed_queue():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='collector_tasks', durable=True)
    
    raw_dir = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\data_raw"
    count = 0
    for filename in os.listdir(raw_dir):
        if filename.endswith(".pdf") and os.path.getsize(os.path.join(raw_dir, filename)) > 1000:
            task = {
                "type": "process_pdf",
                "path": os.path.join(raw_dir, filename),
                "metadata": {"source": "hctlu_harvest", "level": 5}
            }
            channel.basic_publish(
                exchange='',
                routing_key='collector_tasks',
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            count += 1
            print(f"Queued: {filename}")
            
    connection.close()
    print(f"--- SUCCESS: Queued {count} harvested documents for ingestion ---")

if __name__ == "__main__":
    feed_queue()
