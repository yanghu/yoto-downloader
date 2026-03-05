from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from downloader import process_download
from urllib.parse import urlparse

app = FastAPI(title="Yoto Downloader API")

class DownloadRequest(BaseModel):
    url: str

@app.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in request.url and "youtu.be" not in request.url:
        raise HTTPException(status_code=400, detail="非法链接")
    
    try:
        # 提取 URL 中的 ID 部分（排除主机名）
        parsed_url = urlparse(request.url)
        url_id = parsed_url.path.lstrip('/')
        if parsed_url.query:
            url_id += f"?{parsed_url.query}"
            
        # 直接由后台任务处理所有下载和元数据
        background_tasks.add_task(process_download, request.url)
        
        return {
            "status": "accepted",
            "id": url_id,
            "message": f"已收到下载请求 [{url_id}]，NAS 已开始处理..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")