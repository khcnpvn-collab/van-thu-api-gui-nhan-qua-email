# 🚀 Hướng dẫn nhanh - Email Processor API

## Setup nhanh (3 bước)

### Bước 1: Setup virtual environment và cài đặt
```bash
cd "/Users/hieunguyentruongminh/Documents/Petro Viet Nam/email-processor"
bash setup.sh
```

### Bước 2: Chạy server
```bash
bash run.sh
```

### Bước 3: Test API
Mở browser: `http://localhost:8000/docs`

---

## Test nhanh bằng cURL

### 1. Health Check
```bash
curl http://localhost:8000/
```

### 2. Gửi Email (không có file)
```bash
curl -X POST "http://localhost:8000/sendDocumentOutgoing" \
  -H "X-API-Key: your-api-key-here" \
  -F 'data={"mailTo":"recipient@example.com","subject":"Công văn số 123","information":{"docNumber":"123/CV","docTime":"15/01/2024","docSigner":"Nguyễn Văn A","docPageNumber":"5","docPriority":"Khẩn","docKeyword":"Công văn","docSecurity":"Thường","docId":"CV-123","returnEmail":"reply@example.com"},"cc":"cc@example.com"}'
```

### 2b. Gửi Email với file đính kèm
```bash
curl -X POST "http://localhost:8000/sendDocumentOutgoing" \
  -H "X-API-Key: your-api-key-here" \
  -F 'data={"mailTo":"recipient@example.com","subject":"Công văn có file","information":{"docNumber":"456/CV","docTime":"16/01/2024","docSigner":"Trần Thị B","docPageNumber":"10","docPriority":"Thường","docKeyword":"Thông báo","docSecurity":"Mật","docId":"CV-456","returnEmail":"info@example.com"}}' \
  -F "files=@/path/to/document.pdf" \
  -F "files=@/path/to/image.jpg"
```

### 3. Nhận Email chưa đọc (có format hợp lệ)
```bash
curl http://localhost:8000/receiveDocumentIncoming \
  -H "X-API-Key: your-api-key-here"
```

**Response sẽ chỉ chứa email có format đúng với đầy đủ thông tin document**

**Lưu ý**: Email đã parse thành công sẽ tự động được đánh dấu đã đọc

---

## Test với Python script

### Test API cơ bản
```bash
source venv/bin/activate
python test_api.py
```

### Test API với FormData và file attachments
```bash
source venv/bin/activate
python test_formdata_api.py
```

### Test logic xử lý CC
```bash
source venv/bin/activate
python test_cc_logic.py
```

### Test với format template mới
```bash
source venv/bin/activate
python test_new_format.py
```

### Test parser email body
```bash
source venv/bin/activate
python test_parse_email.py
```

### Test API receive incoming
```bash
source venv/bin/activate
python test_receive_api.py
```

### Test tính năng mark as read
```bash
source venv/bin/activate
python test_mark_as_read.py
```
(Test này sẽ gọi API 2 lần để kiểm tra email đã được đánh dấu đã đọc)

---

## Troubleshooting

### ❌ Lỗi: "Virtual environment chưa được tạo"
**Giải pháp:** Chạy `bash setup.sh` trước

### ❌ Lỗi: "Permission denied"
**Giải pháp:** Chạy `chmod +x setup.sh run.sh`

### ❌ Lỗi 401 khi gửi/nhận email
**Giải pháp:** Kiểm tra thông tin trong `.env` và quyền Azure App

### ❌ Lỗi khi cài đặt packages
**Giải pháp:** Đã fix bằng cách dùng virtual environment và cập nhật packages

---

## Tắt server

Nhấn `Ctrl + C` trong terminal đang chạy server

Hoặc:
```bash
pkill -f "python main.py"
```

---

## Tài liệu đầy đủ

Xem file `README.md` để có hướng dẫn chi tiết hơn.

