#!/bin/bash

# Script deploy nhanh lên server

echo "=========================================="
echo "  DEPLOY EMAIL PROCESSOR API"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config
CONTAINER_NAME="email-processor-api"

echo ""
echo "📦 Bước 1: Stop container cũ..."
docker-compose down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container đã stop${NC}"
else
    echo -e "${YELLOW}⚠️  Không có container nào đang chạy${NC}"
fi

echo ""
echo "🔨 Bước 2: Build image mới..."
docker-compose build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build thành công${NC}"
else
    echo -e "${RED}❌ Build thất bại${NC}"
    exit 1
fi

echo ""
echo "🚀 Bước 3: Start container..."
docker-compose up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container đã start${NC}"
else
    echo -e "${RED}❌ Start thất bại${NC}"
    exit 1
fi

echo ""
echo "⏳ Đợi container khởi động (10 giây)..."
sleep 10

echo ""
echo "🔍 Bước 4: Kiểm tra health..."
HEALTH_CHECK=$(curl -sf http://localhost:8000/ || echo "FAIL")

if [ "$HEALTH_CHECK" != "FAIL" ]; then
    echo -e "${GREEN}✅ API đang hoạt động!${NC}"
    echo "$HEALTH_CHECK"
else
    echo -e "${RED}❌ API không phản hồi${NC}"
    echo ""
    echo "📋 Logs:"
    docker logs $CONTAINER_NAME --tail 30
    exit 1
fi

echo ""
echo "📊 Bước 5: Kiểm tra container status..."
docker ps | grep $CONTAINER_NAME

echo ""
echo "📈 Resource usage:"
docker stats $CONTAINER_NAME --no-stream

echo ""
echo "=========================================="
echo -e "${GREEN}✅ DEPLOYMENT HOÀN TẤT!${NC}"
echo "=========================================="
echo ""
echo "📚 Các lệnh hữu ích:"
echo "  - Xem logs:          docker-compose logs -f"
echo "  - Xem stats:         docker stats $CONTAINER_NAME"
echo "  - Restart:           docker-compose restart"
echo "  - Stop:              docker-compose down"
echo "  - Health check:      ./check_container_health.sh"
echo ""
echo "🌐 API endpoints:"
echo "  - Health:            http://localhost:8000/"
echo "  - Docs:              http://localhost:8000/docs"
echo ""

