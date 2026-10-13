import os
from pathlib import Path
from urllib.parse import quote

import grpc
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from proto import file_service_pb2, file_service_pb2_grpc


app = FastAPI(title="File Converter")
GRPC_HOST = os.getenv("GRPC_HOST", "api:50051")


def get_grpc_stub():
    channel = grpc.insecure_channel(
        GRPC_HOST,
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )
    return channel, file_service_pb2_grpc.FileServiceStub(channel)


@app.get("/favicon.svg")
def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
    <rect width="64" height="64" rx="15" fill="#242424"/>
    <path d="M18 10h20l10 10v34H18z" fill="#fff"/>
    <path d="M38 10v12h10" fill="#d9d9d9"/>
    <path d="M25 34h16M25 41h11" stroke="#555" stroke-width="3" stroke-linecap="round"/>
    <path d="M29 28l5-5 5 5M34 23v10" fill="none" stroke="#3978f6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>File Converter — конвертация файлов</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<style>
*{box-sizing:border-box}body{font-family:Arial,sans-serif;background:#f3f5f8;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:24px;color:#202124}
.container{background:white;width:100%;max-width:540px;padding:36px;border-radius:20px;box-shadow:0 14px 45px rgba(0,0,0,.09)}
.logo{width:54px;height:54px;margin:0 auto 16px;border-radius:15px;display:grid;place-items:center;background:#242424;color:white;font-size:27px}
h1{text-align:center;margin:0;font-size:30px}.subtitle{text-align:center;color:#687080;line-height:1.5;margin:12px 0 26px}
label{display:block;font-weight:600;margin:18px 0 8px}input,select,button{width:100%;padding:13px;border-radius:10px;font-size:15px}
input,select{border:1px solid #d5d9e0;background:white}button{margin-top:20px;cursor:pointer;background:#242424;color:white;border:0;font-weight:600}
button:hover{background:#414141}button:disabled{opacity:.6;cursor:wait}.hint{font-size:13px;color:#7a8290;margin-top:9px}
.status{display:none;margin-top:24px;padding:18px;border-radius:12px;background:#f3f5f8;overflow-wrap:anywhere}.status h2{margin:0 0 8px;font-size:19px}.status p{color:#606775;line-height:1.5}
.download{display:block;text-align:center;text-decoration:none;padding:13px;border-radius:10px;background:#176b43;color:white;font-weight:600;margin-top:14px}.download:hover{background:#125535}
.download[hidden],button[hidden]{display:none!important}.secondary{background:#e9ecf1;color:#242424}.secondary:hover{background:#dce1e9}
@media(max-width:480px){.container{padding:24px}h1{font-size:25px}}
</style>
</head>
<body>
<main class="container">
<div class="logo" aria-hidden="true">⇧</div>
<h1>File Converter</h1>
<p class="subtitle">Простой способ конвертировать ваши файлы</p>
<form id="convert-form" action="/convert" method="post" enctype="multipart/form-data">
<label for="file">Выберите файл</label><input id="file" type="file" name="file" required>
<p class="hint">Для первого теста используйте небольшой файл.</p>
<label for="format">Формат результата</label>
<select id="format" name="target_format"><option value="pdf">PDF</option><option value="txt">TXT</option></select>
<button id="submit-button" type="submit">Конвертировать</button>
</form>
<section id="status-box" class="status" aria-live="polite">
<h2 id="status-title">Задача создана</h2><p id="status-text">Ожидаем результат...</p>
<a id="download-link" class="download" hidden>Скачать результат</a>
<button id="again-button" class="secondary" type="button" hidden>Конвертировать ещё</button>
</section>
<section class="history">
  <h2>История конвертаций</h2>
  <button id="history-button" type="button" class="secondary">
    Обновить историю
  </button>
  <p id="history-message">Загрузка истории...</p>
  <div id="history-list"></div>
</section>
</main>
<script>
const form=document.getElementById('convert-form');
const submitButton=document.getElementById('submit-button');
const statusBox=document.getElementById('status-box');
const statusTitle=document.getElementById('status-title');
const statusText=document.getElementById('status-text');
const downloadLink=document.getElementById('download-link');
const againButton=document.getElementById('again-button');

const historyButton = document.getElementById('history-button');
const historyMessage = document.getElementById('history-message');
const historyList = document.getElementById('history-list');

const historyLabels = {
  QUEUED: 'В очереди',
  PROCESSING: 'Обрабатывается',
  COMPLETED: 'Завершено',
  FAILED: 'Ошибка'
};

async function loadHistory() {
  historyButton.disabled = true;
  historyMessage.textContent = 'Загружаем историю...';
  historyList.replaceChildren();

  try {
    const response = await fetch('/api/history');
    const data = await readResponse(response);

    if (data.tasks.length === 0) {
      historyMessage.textContent = 'История пока пуста.';
      return;
    }

    historyMessage.textContent = '';

    for (const task of data.tasks) {
              
      const item = document.createElement('div');
      item.style.cssText =
        'background:#f3f5f8;padding:14px;border-radius:10px;margin-top:10px;overflow-wrap:anywhere';

      const title = document.createElement('strong');
      title.textContent = task.filename;

      const statusColors = {
      QUEUED: '#b45309',
      PROCESSING: '#2563eb',
      COMPLETED: '#15803d',
      FAILED: '#dc2626'
    };

const details = document.createElement('p');
details.textContent =
  `${task.target_format.toUpperCase()} · ${historyLabels[task.status] || task.status}`;
details.style.cssText =
  `color:${statusColors[task.status] || '#475569'};font-weight:600;margin-bottom:0`;

item.append(title, details);

      if (task.error_message) {
        const error = document.createElement('p');
        error.textContent = task.error_message;
        item.append(error);
      }

      if (task.status === 'COMPLETED') {
        const link = document.createElement('a');
        link.href = '/download/' + encodeURIComponent(task.task_id);
        link.textContent = 'Скачать результат';
        link.className = 'download';
        item.append(link);
      }

      historyList.append(item);
    }
  } catch (error) {
    historyMessage.textContent = 'Не удалось загрузить историю: ' + error.message;
  } finally {
    historyButton.disabled = false;
  }
}

historyButton.addEventListener('click', loadHistory);
loadHistory();

const labels={QUEUED:'В очереди',PROCESSING:'Обрабатывается',COMPLETED:'Конвертация завершена!',FAILED:'Не удалось конвертировать файл'};
async function readResponse(response){
 const text=await response.text(); let data;
 try{data=JSON.parse(text)}catch(_){throw new Error(text.slice(0,180)||'Сервер вернул пустой ответ')}
 if(!response.ok)throw new Error(data.detail||'Запрос завершился ошибкой'); return data;
}
form.addEventListener('submit',async event=>{
 event.preventDefault();submitButton.disabled=true;submitButton.textContent='Отправляем файл...';
 statusBox.style.display='block';statusTitle.textContent='Отправка файла';statusText.textContent='Пожалуйста, подождите.';
 downloadLink.hidden=true;downloadLink.removeAttribute('href');againButton.hidden=true;
 try{
  const response=await fetch('/convert',{method:'POST',body:new FormData(form)});const data=await readResponse(response);
  statusText.textContent='ID задачи: '+data.task_id;statusTitle.textContent='Файл принят!';form.style.display='none';await checkStatus(data.task_id);
 }catch(error){statusTitle.textContent='Ошибка';statusText.textContent=error.message;submitButton.disabled=false;submitButton.textContent='Попробовать снова';}
});
async function checkStatus(taskId){
 for(let attempt=0;attempt<120;attempt++){
  try{
   const response=await fetch('/api/status/'+encodeURIComponent(taskId));const data=await readResponse(response);
   statusTitle.textContent=labels[data.status]||data.status;
   statusText.textContent=data.error_message||('ID задачи: '+taskId);
   
if(data.status==='COMPLETED'){
    downloadLink.href='/download/'+encodeURIComponent(taskId);
    downloadLink.hidden=false;
    downloadLink.textContent='Скачать '+(data.target_format||'файл').toUpperCase();
    againButton.hidden=false;
    await loadHistory();
    return;
   }

   if(data.status==='FAILED'){againButton.hidden=false;return;}
  }catch(error){statusTitle.textContent='Не удалось проверить статус';statusText.textContent=error.message;}
  await new Promise(resolve=>setTimeout(resolve,2000));
 }
 statusTitle.textContent='Обработка занимает больше времени';statusText.textContent='Задача ещё не завершена. Попробуйте обновить страницу позже.';againButton.hidden=false;
}
againButton.addEventListener('click',()=>window.location.reload());
</script>
</body>
</html>"""


@app.post("/convert")
async def convert(file: UploadFile = File(...), target_format: str = Form(...)):
    if target_format not in {"pdf", "txt"}:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Выберите файл")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")

    channel, stub = get_grpc_stub()
    try:
        result = stub.UploadFile(
            file_service_pb2.UploadFileRequest(
                filename=Path(file.filename).name,
                content=content,
                target_format=target_format,
            ),
            timeout=30,
        )
        return JSONResponse({"task_id": result.task_id, "status": result.status})
    except grpc.RpcError as exc:
        raise HTTPException(status_code=502, detail=exc.details() or "Ошибка gRPC") from exc
    finally:
        channel.close()


@app.get("/api/status/{task_id}")
def task_status(task_id: str):
    channel, stub = get_grpc_stub()
    try:
        result = stub.GetTaskStatus(
            file_service_pb2.TaskStatusRequest(task_id=task_id),
            timeout=10,
        )
        return {
            "task_id": result.task_id,
            "filename": result.filename,
            "target_format": result.target_format,
            "status": result.status,
            "result_filename": result.result_filename,
            "error_message": result.error_message,
        }
    except grpc.RpcError as exc:
        code = 404 if exc.code() == grpc.StatusCode.NOT_FOUND else 502
        raise HTTPException(status_code=code, detail=exc.details() or "Ошибка gRPC") from exc
    finally:
        channel.close()


@app.get("/api/history")
def task_history(limit: int = 20):
    limit = max(1, min(limit, 100))
    channel, stub = get_grpc_stub()

    try:
        result = stub.GetTaskHistory(
            file_service_pb2.TaskHistoryRequest(limit=limit),
            timeout=10,
        )

        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "filename": task.filename,
                    "target_format": task.target_format,
                    "result_filename": task.result_filename,
                    "status": task.status,
                    "error_message": task.error_message,
                    "created_at": task.created_at,
                }
                for task in result.tasks
            ]
        }
    except grpc.RpcError as exc:
        raise HTTPException(
            status_code=502,
            detail=exc.details() or "Ошибка gRPC",
        ) from exc
    finally:
        channel.close()

@app.get("/download/{task_id}")
def download_result(task_id: str):
    channel, stub = get_grpc_stub()
    try:
        status = stub.GetTaskStatus(
            file_service_pb2.TaskStatusRequest(task_id=task_id), timeout=10
        )
        if status.status != "COMPLETED":
            raise HTTPException(status_code=409, detail="Результат ещё не готов")

        chunks = stub.DownloadResult(
            file_service_pb2.DownloadRequest(task_id=task_id), timeout=60
        )
        data = b"".join(chunk.content for chunk in chunks)
        if not data:
            raise HTTPException(status_code=404, detail="Результат пустой")

        filename = Path(status.result_filename or f"result.{status.target_format}").name
        ascii_name = "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in filename)
        disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
        media_type = "application/pdf" if status.target_format.lower() == "pdf" else "text/plain; charset=utf-8"
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": disposition},
        )
    except grpc.RpcError as exc:
        code = 404 if exc.code() == grpc.StatusCode.NOT_FOUND else 502
        raise HTTPException(status_code=code, detail=exc.details() or "Ошибка gRPC") from exc
    finally:
        channel.close()
