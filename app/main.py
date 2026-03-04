import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import yt_dlp
from PIL import Image

app = FastAPI(title="Yoto Downloader API")
DOWNLOAD_DIR = "/downloads"

class DownloadRequest(BaseModel):
    url: str

def crop_thumbnail_to_square(title: str):
    """查找下载的图片，并将其居中裁剪为 1:1 正方形的 JPG"""
    valid_exts = ['.jpg', '.webp', '.png']
    img_path = None
    
    # yt-dlp 可能会保存为不同的图片格式，先找到它
    for ext in valid_exts:
        potential_path = os.path.join(DOWNLOAD_DIR, f"{title}{ext}")
        if os.path.exists(potential_path):
            img_path = potential_path
            break

    if not img_path:
        print(f"未找到缩略图: {title}")
        return

    try:
        with Image.open(img_path) as img:
            width, height = img.size
            if width == height:
                return # 已经是正方形，无需处理

            # 计算居中裁剪的坐标
            new_size = min(width, height)
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2

            img_cropped = img.crop((left, top, right, bottom))
            
            # 转换为 RGB (防止 webp 带透明通道保存为 jpg 时报错)
            if img_cropped.mode in ("RGBA", "P"):
                img_cropped = img_cropped.convert("RGB")
            
            # 统一保存为标准的 .jpg
            out_path = os.path.join(DOWNLOAD_DIR, f"{title}.jpg")
            img_cropped.save(out_path, "JPEG", quality=95)
            
            # 如果原始图片不是 jpg，清理掉原图保持目录干净
            if img_path != out_path:
                os.remove(img_path)
                
            print(f"图片已成功裁剪为正方形: {out_path}")
            
    except Exception as e:
        print(f"处理图片时出错: {e}")

def process_download(url: str):
    """后台下载任务"""
    ydl_opts: dict = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
        'writethumbnail': True,
        'updatetime': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取信息并下载
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title') or 'Unknown Title'  # Ensure title is always a string

            # 下载完成后，处理图片
            crop_thumbnail_to_square(title)
    except Exception as e:
        print(f"下载失败 {url}: {e}")

@app.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    # 简单的基础校验
    if "youtube.com" not in request.url and "youtu.be" not in request.url:
        raise HTTPException(status_code=400, detail="看起来不是合法的 YouTube 链接")
    
    # 将下载任务放入后台队列，立刻给手机返回成功响应
    background_tasks.add_task(process_download, request.url)
    
    return {
        "status": "success", 
        "message": "任务已接收，NAS 正在后台努力下载和裁剪！"
    }