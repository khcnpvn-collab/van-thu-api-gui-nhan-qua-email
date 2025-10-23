#!/bin/bash

# Script tự động setup virtual environment và cài đặt dependencies

echo "=========================================="
echo "Email Processor API - Setup Script"
echo "=========================================="

# Tạo virtual environment nếu chưa có
if [ ! -d "venv" ]; then
    echo "Đang tạo virtual environment..."
    python3 -m venv venv
    echo "✓ Đã tạo virtual environment"
else
    echo "✓ Virtual environment đã tồn tại"
fi

# Activate virtual environment và cài đặt dependencies
echo ""
echo "Đang kích hoạt virtual environment và cài đặt dependencies..."
source venv/bin/activate

# Upgrade pip
echo "Đang upgrade pip..."
pip install --upgrade pip

# Cài đặt requirements
echo ""
echo "Đang cài đặt dependencies từ requirements.txt..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✓ Setup hoàn tất!"
echo "=========================================="
echo ""
echo "Để chạy ứng dụng:"
echo "  1. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Chạy server:"
echo "     python main.py"
echo ""
echo "  3. Hoặc với uvicorn:"
echo "     uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  4. Truy cập API docs:"
echo "     http://localhost:8000/docs"
echo ""
echo "Để thoát virtual environment:"
echo "  deactivate"
echo "=========================================="

