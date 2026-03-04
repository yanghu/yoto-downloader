import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import yt_dlp
from PIL import Image

app = FastAPI(title="Yoto Downloader API")
DOWNLOAD_DIR = "/downloads"

class DownloadRequest(BaseModel):
    url: str

def crop_thumbnail_to_square(img_path: str):
    """将指定的图片居中裁剪为 1:1 正方形并覆盖保存"""
    if not img_path or not os.path.exists(img_path):
        print(f"未找到缩略图去裁剪: {img_path}")
        return

    try:
        with Image.open(img_path) as img:
            width, height = img.size
            if width == height:
                print(f"图片已经是正方形，无需裁剪: {img_path}")
                return

            # 计算居中裁剪的坐标
            new_size = min(width, height)
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2

            img_cropped = img.crop((left, top, right, bottom))
            
            # 转换为 RGB (防止带有透明通道的格式报错)
            if img_cropped.mode in ("RGBA", "P"):
                img_cropped = img_cropped.convert("RGB")
            
            # 直接覆盖原始的 jpg 文件
            img_cropped.save(img_path, "JPEG", quality=95)
            print(f"图片已成功裁剪为正方形: {img_path}")
            
    except Exception as e:
        print(f"处理图片时出错: {e}")

def process_download(url: str):
    """后台下载任务"""
    ydl_opts: yt_dlp._Params = {  # Explicitly annotate as _Params
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'postprocessors': [
            {
                # 提取音频，改为 m4a (速度更快，不二次损耗音质)
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a', 
            },
            {
                # 核心修复 1：让 ffmpeg 直接把下载的 webp 封面转换为 jpg
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg', 
            }
        ],
        'writethumbnail': True,
        'updatetime': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 核心修复 2：先提取信息，不马上下载
            info_dict = ydl.extract_info(url, download=False)
            
            # 获取 yt-dlp 真正会使用的、经过特殊字符过滤的文件名路径 (不含后缀)
            # 例如: /downloads/歌曲名 _ 过滤版
            base_filename = os.path.splitext(ydl.prepare_filename(info_dict))[0]
            
            # 开始真正的下载
            ydl.download([url])
            
            # 因为我们在 postprocessors 里强制了转 jpg，所以现在的图片路径 100% 确定是这个
            img_path = f"{base_filename}.jpg"
            
            # 去裁剪这张精确找到的图片
            crop_thumbnail_to_square(img_path)
            
    except Exception as e:
        print(f"下载失败 {url}: {e}")

@app.post("/download")
async def trigger_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in request.url and "youtu.be" not in request.url:
        raise HTTPException(status_code=400, detail="看起来不是合法的 YouTube 链接")
    
    background_tasks.add_task(process_download, request.url)
    
    return {
        "status": "success", 
        "message": "任务已接收，NAS 正在后台努力下载和裁剪！"
    }