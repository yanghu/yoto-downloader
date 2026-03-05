@echo off
chcp 65001 >nul

:: --- 配置区 ---
set DOCKER_USER=yang517
set IMAGE_NAME=yoto-downloader
set TAG=latest
:: -------------

echo ===========================================
echo 🔨 开始构建并推送 Docker 镜像 (Windows 版)
echo ===========================================

:: 1. 构建镜像
echo.
echo [1/2] 正在构建镜像: %DOCKER_USER%/%IMAGE_NAME%:%TAG% ...
docker build -t %DOCKER_USER%/%IMAGE_NAME%:%TAG% ./app

if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败，请检查 Dockerfile 或网络连接。
    exit /b %errorlevel%
)

:: 2. 推送镜像
echo.
echo [2/2] 正在推送到 Docker Hub...
docker push %DOCKER_USER%/%IMAGE_NAME%:%TAG%

if %errorlevel% neq 0 (
    echo.
    echo ❌ 推送失败，请检查是否已执行 "docker login"。
    exit /b %errorlevel%
)

echo.
echo ===========================================
echo ✅ 镜像处理完成！
echo ===========================================