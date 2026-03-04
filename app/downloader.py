import os
from datetime import datetime
import yt_dlp
from image import crop_thumbnail_to_square
from config import AUDIO_BASE_DIR, COVER_BASE_DIR

def process_download(query: str):
    """后台下载任务，支持直接 URL 或 文本搜索"""
    
    # 1. 动态获取当前本地日期
    now = datetime.now()
    month_folder = now.strftime("%Y-%m") # 例如：2026-03
    day_folder = now.strftime("%d")      # 例如：03
    
    # 2. 动态拼装今天的专属存放路径
    current_audio_dir = os.path.join(AUDIO_BASE_DIR, month_folder, day_folder)
    current_cover_dir = os.path.join(COVER_BASE_DIR, month_folder, day_folder)
    
    # yt-dlp 非常智能，如果 current_audio_dir 这些多级目录不存在，它会自动创建
    
    download_target = query if query.startswith("http") else f"ytsearch1:{query}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': {
            # 将下载路径指向刚刚算出来的今天专属目录
            'default': f'{current_audio_dir}/%(title)s.%(ext)s',
            'thumbnail': f'{current_cover_dir}/%(title)s.%(ext)s',
        },
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a', 
            }
        ],
        'writethumbnail': True,
        'updatetime': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取信息
            info_dict = ydl.extract_info(download_target, download=False)
            if 'entries' in info_dict:
                info_dict = info_dict['entries'][0]
            
            # 获取最终生成的文件名
            filename = ydl.prepare_filename(info_dict)
            base_filename = os.path.splitext(os.path.basename(filename))[0]
            
            # 真正执行下载
            ydl.download([download_target])
            
            # 把今天的动态封面目录传给图片处理器
            crop_thumbnail_to_square(base_filename, current_cover_dir)
            print(f"✅ 成功下载并处理，已归档至 {month_folder}/{day_folder}: {info_dict.get('title')}")
            
    except Exception as e:
        print(f"❌ 下载失败 {query}: {e}")