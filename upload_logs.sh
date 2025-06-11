#!/bin/bash

# 定义变量
CONTAINER_ID="32ea2cfc5afaf57bcde6efb508d0495dd969075342db73034928586448f5393a"
LOG_FILE="/var/lib/docker/containers/$CONTAINER_ID/${CONTAINER_ID}-json.log"
DATE=$(date +'%Y-%m-%d_%H-%M-%S')
S3_BUCKET="s3://cloud-sec-msj/logs/"

# 压缩日志
gzip -c "$LOG_FILE" > "/home/ubuntu/docker_log_$DATE.gz"

# 上传到S3
aws s3 cp "/home/ubuntu/docker_log_$DATE.gz" "$S3_BUCKET"

# 可选：清理老日志
rm -f "/home/ubuntu/docker_log_$DATE.gz"
