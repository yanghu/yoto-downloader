from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from downloader import process_download
from validator import validate_url, extract_url_id, is_duplicate, record_download

app = FastAPI(title="Yoto Downloader API")

class DownloadRequest(BaseModel):
    url: str

@app.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    try:
        validate_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    url_id = extract_url_id(request.url)

    if is_duplicate(request.url):
        return {
            "status": "duplicate",
            "id": url_id,
            "message": f"今日已下载过 [{url_id}]，跳过重复请求"
        }

    try:
        record_download(request.url)

        # 直接由后台任务处理所有下载和元数据
        background_tasks.add_task(process_download, request.url)

        return {
            "status": "accepted",
            "id": url_id,
            "message": f"已收到下载请求 [{url_id}]，NAS 已开始处理..."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")