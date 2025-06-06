#!/bin/bash

# 启动 cron
echo "Starting crond..."
crontab /app/crontab
cron &

# 启动 Flask app
echo "Starting Flask app..."
sleep 60 && python3 app.py
