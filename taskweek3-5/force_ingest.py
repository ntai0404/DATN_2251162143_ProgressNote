import pika
import json

def force_ingest():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='collector_tasks', durable=True)
    
    task = {
        "url": "local",
        "type": "pdf",
        "name": "2021_Quy_định_Học_bổng",
        "path": "data_raw/2021_Quy_định_Học_bổng.pdf"
    }
    
    channel.basic_publish(
        exchange='',
        routing_key='collector_tasks',
        body=json.dumps(task),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print("Force Ingest Task Published for Scholarship PDF")
    connection.close()

if __name__ == "__main__":
    force_ingest()
