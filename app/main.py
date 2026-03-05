from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import yt_dlp
from downloader import process_download

app = FastAPI(title="Yoto Downloader API")

class DownloadRequest(BaseModel):
    url: str

@app.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in request.url and "youtu.be" not in request.url:
        raise HTTPException(status_code=400, detail="非法链接")
    
    try:
        # 1. 快速提取元数据 (不下载)
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_title = info.get('title', '未知视频')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration_string', '未知')

        # 2. 确认理解无误后，将完整任务丢给后台
        background_tasks.add_task(process_download, request.url)
        
        # 3. 立即返回视频信息给手机
        return {
            "status": "accepted",
            "video": {
                "title": video_title,
                "duration": duration,
                "thumbnail": thumbnail
            },
            "message": "确认过眼神，是这首歌！NAS 已开始下载..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析视频信息失败: {str(e)}")