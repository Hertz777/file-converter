import argparse, os, sys, time
from pathlib import Path
import grpc
from proto import file_service_pb2, file_service_pb2_grpc

HOST = os.getenv("GRPC_HOST", "localhost:50051")

def main():
    parser = argparse.ArgumentParser(description="File Converter gRPC client")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("upload"); p.add_argument("file"); p.add_argument("format")
    p = sub.add_parser("status"); p.add_argument("task_id")
    p = sub.add_parser("download"); p.add_argument("task_id"); p.add_argument("output")
    args = parser.parse_args()
    with grpc.insecure_channel(HOST) as channel:
        stub = file_service_pb2_grpc.FileServiceStub(channel)
        if args.cmd == "upload":
            path = Path(args.file)
            r = stub.UploadFile(file_service_pb2.UploadFileRequest(filename=path.name, target_format=args.format, content=path.read_bytes()))
            print(f"task_id={r.task_id} status={r.status}")
        elif args.cmd == "status":
            r = stub.GetTaskStatus(file_service_pb2.TaskStatusRequest(task_id=args.task_id))
            print(f"{r.task_id}: {r.status} {r.result_filename} {r.error_message}")
        else:
            chunks = stub.DownloadResult(file_service_pb2.DownloadRequest(task_id=args.task_id))
            with open(args.output, "wb") as f:
                for chunk in chunks: f.write(chunk.content)
            print(f"saved to {args.output}")

if __name__ == "__main__": main()
