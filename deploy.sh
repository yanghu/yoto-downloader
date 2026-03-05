#!/bin/bash

# --- 配置区 ---
DOCKER_USER="yang517"
IMAGE_NAME="yoto-downloader"
TAG="latest"
# -------------

echo "==========================================="
echo "🔨 开始构建并推送 Docker 镜像"
echo "==========================================="

# 1. 构建镜像
echo -e "\n[1/2] 正在构建镜像: $DOCKER_USER/$IMAGE_NAME:$TAG ..."
docker build -t $DOCKER_USER/$IMAGE_NAME:$TAG ./app

if [ $? -ne 0 ]; then
    echo -e "\n❌ 构建失败，请检查 Dockerfile 或网络连接。"
    exit 1
fi

# 2. 推送镜像
echo -e "\n[2/2] 正在推送到 Docker Hub..."
docker push $DOCKER_USER/$IMAGE_NAME:$TAG

if [ $? -ne 0 ]; then
    echo -e "\n❌ 推送失败，请检查是否已执行 'docker login'。"
    exit 1
fi

echo -e "\n==========================================="
echo "✅ 镜像处理完成！"
echo "==========================================="