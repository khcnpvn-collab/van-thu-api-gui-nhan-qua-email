#!/bin/bash

# Script chạy ứng dụng trong virtual environment

# Kiểm tra venv có tồn tại không
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment chưa được tạo!"
    echo "Vui lòng chạy: bash setup.sh"
    exit 1
fi

# Kill process đang chiếm port 8000 (nếu có)
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🔄 Đang giải phóng port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Activate venv và chạy app
echo "🚀 Đang khởi động Email Processor API..."
source venv/bin/activate
python main.py

