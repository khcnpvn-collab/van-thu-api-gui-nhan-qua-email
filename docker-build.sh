#!/bin/bash

# Script build Docker image

echo "=========================================="
echo "BUILD DOCKER IMAGE - EMAIL PROCESSOR API"
echo "=========================================="

# Build image
echo ""
echo "🔨 Đang build Docker image..."
docker build -t email-processor:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build thành công!"
    echo ""
    echo "📊 Thông tin image:"
    docker images | grep email-processor
    echo ""
    echo "=========================================="
    echo "Để chạy container:"
    echo "  docker-compose up -d"
    echo ""
    echo "Hoặc:"
    echo "  docker run -d -p 8000:8000 \\"
    echo "    -v \$(pwd)/info.txt:/app/info.txt:ro \\"
    echo "    -v \$(pwd)/email_format.txt:/app/email_format.txt:ro \\"
    echo "    --name email-processor-api \\"
    echo "    email-processor:latest"
    echo "=========================================="
else
    echo ""
    echo "❌ Build thất bại!"
    exit 1
fi

