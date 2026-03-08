import os

# 基础下载目录，与 Docker volume 映射的路径保持一致
BASE_DOWNLOAD_DIR = "/downloads"

# 定义顶层的大类目录
AUDIO_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "audio")
COVER_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "covers")

# 归档目录（已加到 Yoto 卡片的歌曲）
ARCHIVE_AUDIO_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "audio")
ARCHIVE_COVER_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "covers")

# 启动时确保所有目录存在
os.makedirs(AUDIO_BASE_DIR, exist_ok=True)
os.makedirs(COVER_BASE_DIR, exist_ok=True)
os.makedirs(ARCHIVE_AUDIO_DIR, exist_ok=True)
os.makedirs(ARCHIVE_COVER_DIR, exist_ok=True)

# Discord Webhook（可选，不设置则不发送通知）
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")