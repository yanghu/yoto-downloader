from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from downloader import process_download

app = FastAPI(title="Yoto Downloader API")

class DownloadRequest(BaseModel):
    url: str

@app.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in request.url and "youtu.be" not in request.url:
        raise HTTPException(status_code=400, detail="看起来不是合法的 YouTube 链接")
    
    # 将下载任务放入后台，立刻响应手机
    background_tasks.add_task(process_download, request.url)
    
    return {
        "status": "success", 
        "message": "任务已接收，NAS 正在努力下载！"
    }