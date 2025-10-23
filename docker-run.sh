#!/bin/bash

# Script chạy container với docker-compose

echo "=========================================="
echo "START EMAIL PROCESSOR API CONTAINER"
echo "=========================================="

# Kiểm tra docker-compose có cài không
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose chưa được cài đặt"
    echo "Vui lòng cài đặt: https://docs.docker.com/compose/install/"
    exit 1
fi

# Kiểm tra file cần thiết
if [ ! -f ".env" ]; then
    echo "❌ Thiếu file .env"
    echo "Vui lòng copy .env.example thành .env và điền thông tin credentials"
    exit 1
fi

if [ ! -f "email_format.txt" ]; then
    echo "❌ Thiếu file email_format.txt"
    echo "Vui lòng tạo file email_format.txt với format template"
    exit 1
fi

# Stop container cũ nếu đang chạy
echo ""
echo "🔄 Dừng container cũ (nếu có)..."
docker-compose down

# Build và start
echo ""
echo "🚀 Đang build và start container..."
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Container đã được start!"
    echo ""
    echo "📊 Trạng thái container:"
    docker-compose ps
    echo ""
    echo "=========================================="
    echo "API đang chạy tại: http://localhost:8000"
    echo "Swagger UI: http://localhost:8000/docs"
    echo ""
    echo "Các lệnh hữu ích:"
    echo "  - Xem logs:        docker-compose logs -f"
    echo "  - Stop container:  docker-compose down"
    echo "  - Restart:         docker-compose restart"
    echo "  - Xem status:      docker-compose ps"
    echo "=========================================="
else
    echo ""
    echo "❌ Không thể start container!"
    exit 1
fi

