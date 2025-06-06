# 使用官方 Python 3.10 镜像作为基础镜像
FROM python:3.10-slim

RUN apt-get update && apt-get install -y cron curl vim

# 设置工作目录（容器内的目录）
WORKDIR /app

# 将当前目录下的文件复制到容器的 /app 目录中
COPY . /app

# 安装依赖（如果有 requirements.txt 文件）
RUN pip install --no-cache-dir -r requirements.txt