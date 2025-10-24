#!/bin/bash

# Script kiểm tra health của container và tự động restart nếu cần

CONTAINER_NAME="email-processor-api"
API_URL="http://localhost:8000/"
LOG_FILE="/var/log/email-processor-health.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Health Check" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Kiểm tra container có đang chạy không
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container không chạy! Đang restart..." | tee -a "$LOG_FILE"
    docker-compose restart
    exit 1
fi

# Kiểm tra API có response không
if ! curl -sf "$API_URL" > /dev/null 2>&1; then
    echo "❌ API không phản hồi! Checking logs..." | tee -a "$LOG_FILE"
    
    # Lấy logs 20 dòng cuối
    echo "--- Container Logs (last 20 lines) ---" | tee -a "$LOG_FILE"
    docker logs "$CONTAINER_NAME" --tail 20 | tee -a "$LOG_FILE"
    
    # Kiểm tra resource usage
    echo "--- Resource Usage ---" | tee -a "$LOG_FILE"
    docker stats "$CONTAINER_NAME" --no-stream | tee -a "$LOG_FILE"
    
    # Restart container
    echo "🔄 Restarting container..." | tee -a "$LOG_FILE"
    docker-compose restart
    
    # Đợi container start
    sleep 10
    
    # Check lại
    if curl -sf "$API_URL" > /dev/null 2>&1; then
        echo "✅ Container đã restart thành công" | tee -a "$LOG_FILE"
    else
        echo "❌ Container vẫn không hoạt động sau restart" | tee -a "$LOG_FILE"
    fi
else
    echo "✅ Container hoạt động bình thường" | tee -a "$LOG_FILE"
fi

# Kiểm tra resource usage
MEMORY=$(docker stats "$CONTAINER_NAME" --no-stream --format "{{.MemPerc}}" | sed 's/%//')
CPU=$(docker stats "$CONTAINER_NAME" --no-stream --format "{{.CPUPerc}}" | sed 's/%//')

echo "📊 CPU: ${CPU}% | Memory: ${MEMORY}%" | tee -a "$LOG_FILE"

# Cảnh báo nếu resource cao
if (( $(echo "$MEMORY > 80" | bc -l) )); then
    echo "⚠️ WARNING: Memory usage cao (${MEMORY}%)" | tee -a "$LOG_FILE"
fi

if (( $(echo "$CPU > 80" | bc -l) )); then
    echo "⚠️ WARNING: CPU usage cao (${CPU}%)" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

