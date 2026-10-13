FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto ./proto

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/file_service.proto

COPY app ./app
COPY web ./web
COPY tests ./tests
COPY client.py .

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.server"]