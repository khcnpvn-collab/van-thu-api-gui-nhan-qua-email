# Email Processor API

API để xử lý email thông qua Microsoft Graph API, hỗ trợ gửi và nhận email từ tài khoản Microsoft 365.

## Yêu cầu hệ thống

- Python 3.8+
- Tài khoản Microsoft 365 với quyền truy cập Graph API
- Azure App Registration với các quyền:
  - `Mail.Send`
  - `Mail.Read`
  - `Mail.ReadWrite`

## Cài đặt

### 1. Setup Virtual Environment và cài đặt dependencies

**Cách 1: Sử dụng script tự động (Khuyến nghị)**

```bash
# Cho phép thực thi script
chmod +x setup.sh run.sh

# Chạy setup
bash setup.sh
```

**Cách 2: Setup thủ công**

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình

Tạo file `.env` từ template:

```bash
# Copy file example
cp .env.example .env

# Mở và chỉnh sửa với thông tin thực
nano .env  # hoặc dùng editor khác
```

File `.env` cần có các thông tin sau:

```env
CLIENT_ID=your-client-id-here
TENANT_ID=your-tenant-id-here
CLIENT_SECRET=your-client-secret-here
USER_EMAIL=your-email@domain.com
```

## Chạy ứng dụng

### Chạy development server

**Cách 1: Sử dụng script (Khuyến nghị)**

```bash
bash run.sh
```

**Cách 2: Chạy thủ công**

```bash
# Kích hoạt virtual environment (nếu chưa activate)
source venv/bin/activate

# Chạy server
python main.py

# Hoặc dùng uvicorn với auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Lưu ý:** Nhớ activate virtual environment trước khi chạy!

Server sẽ chạy tại: `http://localhost:8000`

### Thoát virtual environment

```bash
deactivate
```

### Swagger Documentation

Truy cập: `http://localhost:8000/docs` để xem API documentation

## 🔐 Authentication

Tất cả các API endpoints (trừ root `/`) đều yêu cầu API Key authentication.

### Cách sử dụng API Key:

**1. Lấy API Key từ file `.env`:**
```bash
cat .env | grep API_KEY
```

**2. Thêm vào Header khi gọi API:**
```bash
# Ví dụ với curl
curl -X GET "http://localhost:8000/receiveDocumentIncoming" \
  -H "X-API-Key: your-api-key-here"
```

**3. Trong Postman:**
- Vào tab "Headers"
- Thêm key: `X-API-Key`
- Thêm value: API key của bạn

**4. Trong code Python:**
```python
import requests

headers = {
    "X-API-Key": "your-api-key-here"
}

response = requests.post(
    "http://localhost:8000/sendDocumentOutgoing",
    headers=headers,
    data={"data": json.dumps(payload)},
    files=files
)
```

**Lưu ý:**
- API key được generate tự động khi setup
- Bạn có thể thay đổi API key trong file `.env`
- Nếu không có `API_KEY` trong `.env`, authentication sẽ bị tắt (development mode)
- **Xem chi tiết:** [API_SECURITY.md](API_SECURITY.md) để biết thêm về bảo mật API

## API Endpoints

### 1. Health Check

**GET** `/`

Kiểm tra trạng thái hoạt động của API.

**Response:**
```json
{
  "status": "running",
  "message": "Email Processor API đang hoạt động",
  "version": "1.0.0"
}
```

### 2. Gửi Email (Send Document Outgoing)

**POST** `/sendDocumentOutgoing`

Gửi email công văn đi với file đính kèm thông qua Microsoft Graph API.

**Request Type:** `multipart/form-data`

**Form Fields:**
- `data` (required): JSON string chứa thông tin email
- `files` (optional): Danh sách file đính kèm (có thể gửi nhiều file)

**JSON trong field `data`:**
```json
{
  "mailTo": "abc@company.com",
  "subject": "Công văn số 123/CV",
  "information": {
    "docNumber": "123/CV-2024",
    "docTime": "15/01/2024 10:30",
    "docSigner": "Nguyễn Văn A - Giám đốc",
    "docPageNumber": "5",
    "docPriority": "Khẩn",
    "docKeyword": "Công văn, Báo cáo",
    "docSecurity": "Thường",
    "docId": "CV-2024-123",
    "returnEmail": "reply@company.com"
  },
  "cc": "manager@company.com"
}
```

**Parameters trong JSON:**
- `mailTo` (required): Email người nhận (có thể nhiều email cách nhau bởi dấu phẩy hoặc chấm phẩy)
- `subject` (required): Tiêu đề email
- `information` (required): Object chứa thông tin công văn
  - `docNumber`: Số công văn
  - `docTime`: Thời gian công văn
  - `docSigner`: Người ký
  - `docPageNumber`: Số trang
  - `docPriority`: Độ ưu tiên
  - `docKeyword`: Từ khóa
  - `docSecurity`: Độ mật
  - `docId`: Mã công văn
  - `returnEmail`: Email phản hồi
- `cc` (optional): Email CC (có thể nhiều email cách nhau bởi dấu phẩy hoặc chấm phẩy)

**Lưu ý về Body Email:**
- Body email được tự động tạo từ format template trong file `email_format.txt`
- Format template sử dụng các placeholder như `{docNumber}`, `{docTime}`, v.v.
- Các placeholder sẽ được thay thế bằng giá trị từ field `information`
- Tags XML (như `<DOC>`, `<DOCNUMBER>`) sẽ hiển thị như text trong email (đã được escape HTML)

**Giới hạn:**
- Tổng kích thước file đính kèm: tối đa 25MB
- Hỗ trợ tất cả các loại file

**Response:**
```json
{
  "success": true,
  "message": "Email đã được gửi thành công với 2 file đính kèm",
  "data": {
    "from": "hieu.nguyen@yrh7k.onmicrosoft.com",
    "to": ["abc@company.com"],
    "cc": ["manager@company.com"],
    "subject": "Công văn số 123/CV",
    "attachments": [
      {
        "filename": "document1.pdf",
        "size": 12345,
        "content_type": "application/pdf"
      },
      {
        "filename": "document2.docx",
        "size": 23456,
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      }
    ],
    "total_attachment_size": "35.00 KB"
  }
}
```

**Ví dụ cURL:**

Gửi email KHÔNG có file:
```bash
curl -X POST "http://localhost:8000/sendDocumentOutgoing" \
  -H "X-API-Key: your-api-key-here" \
  -F 'data={"mailTo":"abc@company.com","subject":"Công văn số 123","information":{"docNumber":"123/CV","docTime":"15/01/2024","docSigner":"Nguyễn Văn A","docPageNumber":"5","docPriority":"Khẩn","docKeyword":"Công văn","docSecurity":"Thường","docId":"CV-123","returnEmail":"reply@example.com"},"cc":"manager@company.com"}'
```

Gửi email VÀ có file đính kèm:
```bash
curl -X POST "http://localhost:8000/sendDocumentOutgoing" \
  -H "X-API-Key: your-api-key-here" \
  -F 'data={"mailTo":"abc@company.com","subject":"Công văn số 456","information":{"docNumber":"456/CV","docTime":"16/01/2024","docSigner":"Trần Thị B","docPageNumber":"10","docPriority":"Thường","docKeyword":"Thông báo","docSecurity":"Mật","docId":"CV-456","returnEmail":"info@example.com"}}' \
  -F "files=@/path/to/document1.pdf" \
  -F "files=@/path/to/document2.docx"
```

Gửi email với 1 file:
```bash
curl -X POST "http://localhost:8000/sendDocumentOutgoing" \
  -H "X-API-Key: your-api-key-here" \
  -F 'data={"mailTo":"abc@company.com","subject":"Công văn có file","information":{"docNumber":"789/CV","docTime":"17/01/2024","docSigner":"Lê Văn C","docPageNumber":"3","docPriority":"Hỏa tốc","docKeyword":"Khẩn cấp","docSecurity":"Tối mật","docId":"CV-789","returnEmail":"emergency@example.com"}}' \
  -F "files=@document.pdf"
```

### 3. Nhận Email (Receive Document Incoming)

**GET** `/receiveDocumentIncoming`

Kiểm tra và lấy danh sách email chưa đọc có format hợp lệ từ hộp thư.

**Chức năng:**
- Lấy tất cả email chưa đọc
- Parse body theo format template trong `email_format.txt`
- Chỉ trả về email có format đúng (chứa tags `<DOC>`, `<DOCNUMBER>`, v.v.)
- Extract thông tin document từ email body
- **Tự động đánh dấu đã đọc**: Email đã parse thành công sẽ được đánh dấu là đã đọc để lần sau không lấy lại

**Response:**
```json
{
  "length": 2,
  "data": [
    {
      "subject": "Công văn số 123/CV",
      "sentFrom": "sender@company.com",
      "docNumber": "123/CV-2024",
      "docTime": "15/01/2024 10:30",
      "docSigner": "Nguyễn Văn A",
      "docPageNumber": "5",
      "docPriority": "Khẩn",
      "docKeyword": "Công văn",
      "docSecurity": "Thường",
      "docId": "CV-2024-123",
      "returnEmail": "reply@company.com",
      "messageId": "AAMkAGI...",
      "receivedDateTime": "2025-10-23T10:30:00Z"
    },
    {
      "subject": "Công văn số 456/CV",
      "sentFrom": "other@company.com",
      "docNumber": "456/CV-2024",
      "docTime": "16/01/2024",
      "docSigner": "Trần Thị B",
      "docPageNumber": "10",
      "docPriority": "Thường",
      "docKeyword": "Thông báo",
      "docSecurity": "Mật",
      "docId": "CV-2024-456",
      "returnEmail": "info@company.com",
      "messageId": "AAMkAGI...",
      "receivedDateTime": "2025-10-23T11:00:00Z"
    }
  ]
}
```

**Lưu ý:**
- Chỉ trả về email có đầy đủ các field theo format
- Email không đúng format sẽ bị bỏ qua (và KHÔNG được đánh dấu đã đọc)
- Email đã parse thành công sẽ tự động được đánh dấu đã đọc
- Lần gọi API tiếp theo sẽ không lấy lại email đã đọc
- Parser hỗ trợ cả email đã escape HTML (`&lt;`, `&gt;`) và plain text

**Ví dụ cURL:**
```bash
curl -X GET "http://localhost:8000/receiveDocumentIncoming" \
  -H "X-API-Key: your-api-key-here"
```

## Parsing Rules

API `/receiveDocumentIncoming` parse email body theo các quy tắc sau:

1. Email phải chứa tags `<DOC>` và `</DOC>`
2. Phải có đầy đủ 9 fields:
   - `<DOCNUMBER>`, `<DOCTIME>`, `<DOCSIGNER>`
   - `<DOCPAGENUMBER>`, `<DOCPRIORITY>`, `<DOCKEYWORD>`
   - `<DOCSECURITY>`, `<DOCID>`, `<RETURN-EMAIL>`
3. Parser tự động:
   - Unescape HTML (`&lt;` → `<`, `&gt;` → `>`)
   - Loại bỏ HTML tags (`<pre>`, `<div>`, v.v.)
   - Extract giá trị giữa các tags
4. Email thiếu field hoặc không đúng format sẽ bị bỏ qua

## Xử lý lỗi

API trả về các mã lỗi HTTP chuẩn:

- `200`: Success
- `400`: Bad Request (thiếu thông tin hoặc dữ liệu không hợp lệ)
- `500`: Internal Server Error (lỗi khi gọi Graph API hoặc lỗi server)

**Ví dụ error response:**
```json
{
  "detail": "Lỗi khi gửi email: 401 - Unauthorized"
}
```

## Cấu trúc Project

```
email-processor/
├── main.py                 # FastAPI application chính
├── config.py               # Cấu hình và load credentials
├── graph_service.py        # Service layer cho Graph API
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (không commit lên git)
├── .env.example           # Template cho .env
├── email_format.txt       # Format template cho email body
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore          # Files bỏ qua khi build Docker
├── docker-build.sh        # Script build Docker image
├── docker-run.sh          # Script chạy container
├── README.md              # Tài liệu hướng dẫn
├── FORMAT_GUIDE.md        # Hướng dẫn chi tiết về format
├── API_SECURITY.md        # Hướng dẫn bảo mật API
├── QUICKSTART.md          # Hướng dẫn nhanh
├── DEPLOYMENT.md          # Hướng dẫn deploy
└── MIGRATION_TO_ENV.md    # Hướng dẫn migration từ info.txt sang .env
```

## Bảo mật

⚠️ **LƯU Ý QUAN TRỌNG:**

- File `.env` chứa thông tin nhạy cảm, **KHÔNG BAO GIỜ** commit lên git
- File `.env` đã được thêm vào `.gitignore`
- Chỉ commit file `.env.example` (template không có thông tin thật)

## Troubleshooting

### Lỗi authentication

Nếu gặp lỗi `401 Unauthorized`:
1. Kiểm tra lại thông tin trong `.env`
2. Đảm bảo Azure App đã được cấp đủ quyền (Mail.Send, Mail.Read, Mail.ReadWrite)
3. Đảm bảo đã thực hiện "Grant admin consent" trong Azure Portal

### Lỗi không gửi được email

1. Kiểm tra email trong `.env` có tồn tại và active
2. Kiểm tra mailbox đã được kích hoạt
3. Kiểm tra network có thể kết nối tới `https://graph.microsoft.com`

## License

MIT

