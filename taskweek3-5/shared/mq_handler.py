import pika
import json
import os

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

def send_task(queue_name, task_data):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(task_data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    print(f"Sent task to {queue_name}")

if __name__ == "__main__":
    # Example usage
    # send_task('collector_tasks', {'type': 'pdf', 'url': 'C:/SINHVIEN/DATN/taskWeek1-2/data_raw/example.pdf'})
    pass
