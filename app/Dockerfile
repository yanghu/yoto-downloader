FROM python:3.11-slim


# 1. 更新 apt 并安装 ffmpeg、curl 和 unzip
# 2. 安装 Deno，并将其移动到全局目录 /usr/local/bin，允许任何非 root 用户 (如 PUID) 调用它
RUN apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/deno && \
    chmod +x /usr/local/bin/deno && \
    rm -rf /root/.deno && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 启动 FastAPI 服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]