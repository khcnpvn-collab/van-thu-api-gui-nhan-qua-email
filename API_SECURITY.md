# API Security - Hướng dẫn bảo mật API

## 🔐 Tổng quan

Email Processor API sử dụng **API Key Authentication** để bảo vệ các endpoints. Tất cả các API (trừ root health check `/`) đều yêu cầu API Key hợp lệ trong header.

## Cấu hình API Key

### 1. Lấy API Key

API Key được tự động generate khi setup project. Xem API Key hiện tại:

```bash
cat .env | grep API_KEY
```

Hoặc:

```bash
echo $API_KEY  # (sau khi source .env)
```

### 2. Thay đổi API Key (khuyến nghị cho production)

**Cách 1: Generate random key an toàn**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Cách 2: Tự đặt key**

Mở file `.env` và thay đổi:

```env
API_KEY=your-new-secure-api-key-here
```

**Lưu ý:**
- API Key nên dài ít nhất 32 ký tự
- Chứa chữ, số và ký tự đặc biệt
- KHÔNG chia sẻ API Key với người khác
- Thay đổi định kỳ (mỗi 3-6 tháng)

### 3. Tắt Authentication (Development Mode)

Nếu muốn tắt authentication để test local, xóa hoặc comment dòng `API_KEY` trong `.env`:

```env
# API_KEY=...  # Commented out = authentication disabled
```

Restart server để áp dụng thay đổi.

## Cách sử dụng API Key

### 1. Với cURL

```bash
curl -X POST "http://localhost:8000/sendDocumentOutgoing" \
  -H "X-API-Key: AYNv9mGgytUXwwP4bO8Ovlg-iKovPK855pMdZyT_AhU" \
  -F 'data={...}'
```

### 2. Với Postman

**Cách A: Thêm vào Headers**
1. Mở tab "Headers"
2. Thêm key: `X-API-Key`
3. Thêm value: API key của bạn

**Cách B: Sử dụng Authorization (nâng cao)**
1. Tab "Authorization"
2. Type: "API Key"
3. Key: `X-API-Key`
4. Value: API key của bạn
5. Add to: "Header"

### 3. Với Python requests

```python
import requests

API_KEY = "AYNv9mGgytUXwwP4bO8Ovlg-iKovPK855pMdZyT_AhU"

headers = {
    "X-API-Key": API_KEY
}

# GET request
response = requests.get(
    "http://localhost:8000/receiveDocumentIncoming",
    headers=headers
)

# POST request với files
files = {
    'files': open('document.pdf', 'rb')
}
data = {
    'data': json.dumps({
        "mailTo": "user@example.com",
        "subject": "Test",
        "information": {...}
    })
}

response = requests.post(
    "http://localhost:8000/sendDocumentOutgoing",
    headers=headers,
    data=data,
    files=files
)
```

### 4. Với JavaScript/Fetch

```javascript
const API_KEY = "AYNv9mGgytUXwwP4bO8Ovlg-iKovPK855pMdZyT_AhU";

// GET request
fetch('http://localhost:8000/receiveDocumentIncoming', {
  method: 'GET',
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));

// POST request với FormData
const formData = new FormData();
formData.append('data', JSON.stringify({
  mailTo: "user@example.com",
  subject: "Test",
  information: {...}
}));
formData.append('files', fileInput.files[0]);

fetch('http://localhost:8000/sendDocumentOutgoing', {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Response khi Authentication thất bại

### Missing API Key

Request không có header `X-API-Key`:

```json
{
  "detail": "Not authenticated"
}
```

Status code: `403 Forbidden`

### Invalid API Key

API Key không đúng:

```json
{
  "detail": "Invalid API Key"
}
```

Status code: `403 Forbidden`

## Best Practices

### 1. Bảo mật API Key

✅ **NÊN:**
- Lưu API Key trong `.env` (đã được gitignore)
- Sử dụng environment variables trong production
- Rotate API Key định kỳ
- Sử dụng HTTPS trong production
- Log failed authentication attempts

❌ **KHÔNG NÊN:**
- Commit `.env` lên Git
- Hardcode API Key trong source code
- Chia sẻ API Key qua email/chat
- Sử dụng API Key đơn giản (như "123456")

### 2. Deployment trên Production

**Với Docker:**

```bash
# Đọc API_KEY từ .env file
docker-compose up -d
```

**Với Docker manual:**

```bash
docker run -d \
  --env-file .env \
  email-processor:latest
```

**Với Kubernetes:**

Sử dụng Secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: email-processor-secrets
type: Opaque
stringData:
  API_KEY: "your-api-key-here"
```

### 3. Multiple API Keys (Nâng cao)

Nếu cần multiple API keys cho nhiều client, bạn có thể customize `verify_api_key()` function trong `main.py`:

```python
# Trong .env
API_KEYS=key1,key2,key3

# Trong main.py
VALID_API_KEYS = os.getenv('API_KEYS', '').split(',')

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

### 4. Rate Limiting (Khuyến nghị thêm)

Để tránh abuse, nên thêm rate limiting. Sử dụng `slowapi`:

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/receiveDocumentIncoming")
@limiter.limit("10/minute")  # 10 requests per minute
async def receive_document_incoming(...):
    ...
```

## Troubleshooting

### Lỗi "Not authenticated"

**Nguyên nhân:** Thiếu header `X-API-Key`

**Giải pháp:**
1. Kiểm tra request có header `X-API-Key` không
2. Kiểm tra tên header (phải là `X-API-Key`, không phải `x-api-key` hoặc `API-Key`)

### Lỗi "Invalid API Key"

**Nguyên nhân:** API Key không đúng

**Giải pháp:**
1. Lấy lại API Key từ `.env`: `cat .env | grep API_KEY`
2. Copy chính xác API Key (không có space, newline)
3. Kiểm tra server đã load `.env` chưa (restart nếu cần)

### API Key không hoạt động sau khi thay đổi

**Nguyên nhân:** Server chưa reload config

**Giải pháp:**
1. Restart server: `./run.sh`
2. Hoặc với Docker: `docker-compose restart`

### Swagger UI không cho phép nhập API Key

**Giải pháp:**
1. Mở Swagger UI: `http://localhost:8000/docs`
2. Click nút "Authorize" ở góc trên bên phải
3. Nhập API Key vào field "X-API-Key"
4. Click "Authorize"
5. Giờ có thể test API trực tiếp từ Swagger

---

## Liên hệ

Nếu có vấn đề về security, vui lòng xem thêm:
- [README.md](README.md) - Tài liệu chính
- [DEPLOYMENT.md](DEPLOYMENT.md) - Hướng dẫn deploy
- [QUICKSTART.md](QUICKSTART.md) - Hướng dẫn nhanh

