FROM python:3.11-slim

# 1. 更新 apt 并安装 ffmpeg、curl 和 unzip
# 2. 用 curl 官方脚本一键安装 Deno (用于破解 YouTube 最新的反爬虫 JS 挑战)
RUN apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    curl -fsSL https://deno.land/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# 将 Deno 加入环境变量，让 yt-dlp 能找到它
ENV PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 启动 FastAPI 服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]