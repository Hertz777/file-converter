import json, time
from pathlib import Path
import pika
from . import db
from .config import RABBITMQ_URL, QUEUE_NAME
from .converter import convert

def callback(ch, method, properties, body):
    task_id = json.loads(body)["task_id"]
    row = db.get_task(task_id)
    if not row:
        ch.basic_ack(method.delivery_tag); return
    _, filename, target_format, source_path, _, _, _, _ = row
    try:
        db.update_task(task_id, "PROCESSING", error_message=None)
        source = Path(source_path)
        result_filename = f"{source.stem.rsplit('_', 1)[0]}_result.{target_format.lstrip('.') }"
        result = source.parent / result_filename
        convert(source, result, target_format)
        db.update_task(task_id, "COMPLETED", str(result), result_filename, None)
        print(f"Task {task_id}: completed", flush=True)
    except Exception as exc:
        db.update_task(task_id, "FAILED", error_message=str(exc))
        print(f"Task {task_id}: failed: {exc}", flush=True)
    finally:
        ch.basic_ack(method.delivery_tag)

def main():
    while True:
        try:
            db.init_db()
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            print("Worker started", flush=True)
            channel.start_consuming()
        except Exception as exc:
            print(f"Worker connection error: {exc}; retrying", flush=True)
            time.sleep(3)

if __name__ == "__main__": main()
