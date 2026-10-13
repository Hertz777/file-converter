from concurrent import futures
from pathlib import Path
from uuid import uuid4
import grpc
from proto import file_service_pb2, file_service_pb2_grpc
from . import db
from .config import GRPC_HOST, STORAGE_DIR
from .queue import publish

class FileService(file_service_pb2_grpc.FileServiceServicer):
    def UploadFile(self, request, context):
        if not request.filename or not request.content or not request.target_format:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "filename, target_format and content are required")
        task_id = uuid4()
        storage = Path(STORAGE_DIR); storage.mkdir(parents=True, exist_ok=True)
        source = storage / f"{task_id}_{Path(request.filename).name}"
        source.write_bytes(request.content)
        db.create_task(task_id, request.filename, request.target_format, str(source))
        publish({"task_id": str(task_id)})
        return file_service_pb2.UploadFileResponse(task_id=str(task_id), status="QUEUED")

    def GetTaskStatus(self, request, context):
        row = db.get_task(request.task_id)
        if not row:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        task_id, filename, target_format, _, _, result_filename, status, error = row
        return file_service_pb2.TaskStatusResponse(task_id=str(task_id), filename=filename, target_format=target_format, status=status, result_filename=result_filename or "", error_message=error or "")

    
    def GetTaskHistory(self, request, context):
        limit = request.limit if request.limit > 0 else 20
        limit = min(limit, 100)

        rows = db.get_recent_tasks(limit)
        tasks = []

        for row in rows:
            task_id, filename, target_format, result_filename, status, error_message, created_at = row

            tasks.append(
                file_service_pb2.TaskHistoryItem(
                    task_id=str(task_id),
                    filename=filename,
                    target_format=target_format,
                    result_filename=result_filename or "",
                    status=status,
                    error_message=error_message or "",
                    created_at=created_at.isoformat(),
                )
            )

        return file_service_pb2.TaskHistoryResponse(tasks=tasks)

    def DownloadResult(self, request, context):
        row = db.get_task(request.task_id)
        if not row:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        if row[6] != "COMPLETED" or not row[4]:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Result is not ready")
        with open(row[4], "rb") as f:
            while chunk := f.read(64 * 1024):
                yield file_service_pb2.FileChunk(content=chunk)

def main():
    db.init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_service_pb2_grpc.add_FileServiceServicer_to_server(FileService(), server)
    server.add_insecure_port(GRPC_HOST)
    server.start()
    print(f"gRPC server started on {GRPC_HOST}", flush=True)
    server.wait_for_termination()

if __name__ == "__main__": main()
