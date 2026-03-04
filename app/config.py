import os

# 基础下载目录，与 Docker volume 映射的路径保持一致
BASE_DOWNLOAD_DIR = "/downloads"

# 定义子目录
AUDIO_DIR = os.path.join(BASE_DOWNLOAD_DIR, "audio")
COVER_DIR = os.path.join(BASE_DOWNLOAD_DIR, "covers")

# 启动时自动确保这些子目录存在
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)