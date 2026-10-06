import json
import time
import pika
from .config import RABBITMQ_URL, QUEUE_NAME

def publish(payload):
    for _ in range(20):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(payload).encode(), properties=pika.BasicProperties(delivery_mode=2))
            connection.close()
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("RabbitMQ unavailable")
