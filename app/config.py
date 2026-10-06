import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://converter:converter@localhost:5432/fileconverter")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0:50051")
QUEUE_NAME = "file_conversion"
