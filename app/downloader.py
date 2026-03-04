import os
import yt_dlp
from image import crop_thumbnail_to_square
from config import AUDIO_DIR, COVER_DIR

def process_download(url: str):
    """后台下载任务"""
    ydl_opts = {
        'format': 'bestaudio/best',
        # 修复：直接利用 outtmpl 字典显式指定不同类型文件的绝对路径，这种方式最稳妥
        'outtmpl': {
            'default': f'{AUDIO_DIR}/%(title)s.%(ext)s',   # 音频文件存入 audio 目录
            'thumbnail': f'{COVER_DIR}/%(title)s.%(ext)s', # 封面图片存入 covers 目录
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
            # 1. 提取信息
            info_dict = ydl.extract_info(url, download=False)
            
            # 2. 获取文件名。由于我们配置了不同的 paths，这里用 os.path.basename 只提取纯净的文件名部分
            filename = ydl.prepare_filename(info_dict)
            base_filename = os.path.splitext(os.path.basename(filename))[0]
            
            # 3. 执行下载
            ydl.download([url])
            
            # 4. 把文件名和目录传给图片处理器进行处理
            crop_thumbnail_to_square(base_filename, COVER_DIR)
            
    except Exception as e:
        print(f"下载失败 {url}: {e}")