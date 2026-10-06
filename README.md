# File Converter Service

Учебный проект по теме «Сервис обработки и конвертации файлов».

## Стек
- Python 3.12
- gRPC + Protocol Buffers
- RabbitMQ
- PostgreSQL
- Docker / Docker Compose
- pytest
- GitHub Actions
- Jenkins (опционально, через Docker)

## Архитектура

Client -> gRPC API -> PostgreSQL + RabbitMQ -> Worker -> файловое хранилище

API принимает файл, создаёт задачу в PostgreSQL и публикует её в RabbitMQ. Worker получает задачу, выполняет конвертацию и обновляет статус.

## Поддерживаемые операции
- TXT -> PDF
- PNG/JPG/JPEG -> PNG
- PNG/JPG/JPEG -> JPEG
- TXT -> TXT (копирование как демонстрация обработки)

## Запуск

Требуется Docker Desktop / Docker Engine с Compose.

```bash
docker compose up --build
```

После запуска:
- gRPC API: `localhost:50051`
- PostgreSQL: `localhost:5432`
- RabbitMQ AMQP: `localhost:5672`
- RabbitMQ UI: http://localhost:15672

RabbitMQ login/password: `guest/guest`.

## Пример клиента

В другом терминале:

```bash
docker compose run --rm client python client.py upload sample.txt pdf
```

Проверить статус:

```bash
docker compose run --rm client python client.py status <TASK_ID>
```

Скачать результат:

```bash
docker compose run --rm client python client.py download <TASK_ID> result.pdf
```

## Тесты

```bash
docker compose run --rm tests
```

## CI/CD

В `.github/workflows/ci.yml` находится GitHub Actions pipeline: сборка образов и запуск тестов.

В `jenkins/` находится `Jenkinsfile`. Jenkins можно запустить локально через Docker, если преподаватель потребует именно Jenkins.

## gRPC методы

- `UploadFile` — загрузка файла и создание задачи
- `GetTaskStatus` — получение статуса
- `DownloadResult` — скачивание результата чанками

Статусы: `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`.
