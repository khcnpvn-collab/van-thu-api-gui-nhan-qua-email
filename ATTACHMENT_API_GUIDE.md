# 📎 Hướng dẫn sử dụng API Attachments - Email Processor

## 📋 Tổng quan

API `receiveDocumentIncoming` đã được cập nhật để **tự động lấy và trả về attachments** của mỗi email.

**Điểm quan trọng:**
- ✅ Attachments được trả về dưới dạng **base64 encoded string**
- ✅ Mỗi attachment có đầy đủ: `name`, `contentType`, `size`, `contentBytes`
- ✅ Frontend có thể dễ dàng convert base64 sang Blob/File và upload lên Supabase
- ✅ API tự động lấy attachments cho mỗi email có format hợp lệ

---

## 🔍 Flow xử lý Attachments

```
1. API nhận request GET /receiveDocumentIncoming
   ↓
2. Lấy danh sách email chưa đọc từ hộp thư
   ↓
3. Parse body của mỗi email theo format template
   ↓
4. Với mỗi email có format hợp lệ:
   a. Gọi Microsoft Graph API để lấy attachments
   b. Mỗi attachment có contentBytes (đã base64)
   c. Đóng gói attachment vào response
   ↓
5. Đánh dấu email đã đọc
   ↓
6. Trả về response với đầy đủ thông tin + attachments
```

---

## 📥 API Endpoint

### **GET /receiveDocumentIncoming**

**Headers:**
```
X-API-Key: your-api-key-here
```

**Response:** (Status 200)
```json
{
  "length": 2,
  "data": [
    {
      "subject": "Công văn số 123/CV",
      "sentFrom": "sender@example.com",
      "docNumber": "123/CV",
      "docTime": "15/01/2024",
      "docSigner": "Nguyễn Văn A",
      "docPageNumber": "5",
      "docPriority": "Khẩn",
      "docKeyword": "Công văn",
      "docSecurity": "Thường",
      "docId": "CV-123",
      "returnEmail": "reply@example.com",
      "messageId": "AAMkAGE3NTY4...",
      "receivedDateTime": "2024-01-15T10:30:00Z",
      "attachments": [
        {
          "name": "document.pdf",
          "contentType": "application/pdf",
          "size": 524288,
          "contentBytes": "JVBERi0xLjQKJeLjz9MKMyAwIG9iaiA8PC9UeXBlIC9QYWdlL1BhcmVudCAyIDAgUi..."
        },
        {
          "name": "image.jpg",
          "contentType": "image/jpeg",
          "size": 153600,
          "contentBytes": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkS..."
        }
      ]
    },
    {
      "subject": "Công văn số 456/CV",
      "sentFrom": "another@example.com",
      "docNumber": "456/CV",
      "docTime": "16/01/2024",
      "docSigner": "Trần Thị B",
      "docPageNumber": "3",
      "docPriority": "Thường",
      "docKeyword": "Thông báo",
      "docSecurity": "Mật",
      "docId": "CV-456",
      "returnEmail": "info@example.com",
      "messageId": "AAMkAGE3NTY5...",
      "receivedDateTime": "2024-01-16T14:20:00Z",
      "attachments": []
    }
  ]
}
```

---

## 🧪 Test API với Python

### Bước 1: Chạy test script

```bash
# Đảm bảo API đang chạy
python test_receive_with_attachments.py
```

Script sẽ:
- ✅ Gọi API `/receiveDocumentIncoming`
- ✅ Hiển thị thông tin documents và attachments
- ✅ Hỏi có muốn download attachments không
- ✅ Decode base64 và lưu files vào thư mục `downloaded_attachments/`

### Bước 2: Test với cURL

```bash
curl -X GET "http://localhost:8000/receiveDocumentIncoming" \
  -H "X-API-Key: your-api-key-here" \
  | jq '.'
```

---

## 💡 Xử lý Attachments trong Code

### Backend (Python)

```python
import requests
import base64
from pathlib import Path

def download_attachments_from_api():
    response = requests.get(
        "http://localhost:8000/receiveDocumentIncoming",
        headers={"X-API-Key": "your-api-key"}
    )
    
    data = response.json()
    
    for doc in data['data']:
        for attachment in doc['attachments']:
            # Decode base64
            file_content = base64.b64decode(attachment['contentBytes'])
            
            # Lưu file
            file_path = Path(f"downloads/{doc['docId']}/{attachment['name']}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            print(f"✅ Saved: {file_path}")
```

### Frontend (JavaScript/TypeScript)

Chi tiết xem file **`FE_ATTACHMENT_GUIDE.md`**

**Tóm tắt:**
```javascript
// Convert base64 sang Blob
function base64ToBlob(base64String, contentType) {
  const byteCharacters = atob(base64String);
  const byteNumbers = new Array(byteCharacters.length);
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: contentType });
}

// Upload lên Supabase
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function uploadToSupabase(attachment, docId) {
  const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
  
  const { data, error } = await supabase.storage
    .from('documents')
    .upload(`${docId}/${attachment.name}`, blob, {
      contentType: attachment.contentType
    });
  
  if (error) throw error;
  
  // Lấy public URL
  const { data: urlData } = supabase.storage
    .from('documents')
    .getPublicUrl(`${docId}/${attachment.name}`);
  
  return urlData.publicUrl;
}

// Sử dụng
const response = await fetch('/receiveDocumentIncoming', {
  headers: { 'X-API-Key': 'your-api-key' }
});

const { data: documents } = await response.json();

for (const doc of documents) {
  for (const att of doc.attachments) {
    const url = await uploadToSupabase(att, doc.docId);
    console.log(`✅ Uploaded: ${url}`);
  }
}
```

---

## 🔍 Chi tiết kỹ thuật

### 1. Microsoft Graph API

API sử dụng endpoint sau để lấy attachments:
```
GET https://graph.microsoft.com/v1.0/users/{userEmail}/messages/{messageId}/attachments
```

**Response từ Graph API:**
```json
{
  "value": [
    {
      "@odata.type": "#microsoft.graph.fileAttachment",
      "id": "AAMkAGE3...",
      "name": "document.pdf",
      "contentType": "application/pdf",
      "size": 524288,
      "contentBytes": "JVBERi0xLjQK..."
    }
  ]
}
```

### 2. Code trong GraphService

```python
def get_message_attachments(self, user_email: str, message_id: str) -> List[Dict]:
    """
    Lấy danh sách attachments của một email
    
    Args:
        user_email: Email người dùng
        message_id: ID của message
    
    Returns:
        List các attachment với thông tin: name, contentType, size, contentBytes (base64)
    """
    token = self.get_access_token()
    
    endpoint = f"{GRAPH_API_ENDPOINT}/users/{user_email}/messages/{message_id}/attachments"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        attachments = []
        
        for attachment in data.get('value', []):
            # Chỉ lấy file attachments (không lấy inline images)
            if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                attachments.append({
                    'name': attachment.get('name', 'unknown'),
                    'contentType': attachment.get('contentType', 'application/octet-stream'),
                    'size': attachment.get('size', 0),
                    'contentBytes': attachment.get('contentBytes', '')  # Đã là base64
                })
        
        return attachments
    else:
        return []
```

### 3. Code trong API receiveDocumentIncoming

```python
# Lấy attachments của email
attachments = []
try:
    if message_id:
        message_attachments = graph_service.get_message_attachments(USER_EMAIL, message_id)
        
        for att in message_attachments:
            attachments.append(AttachmentInfo(
                name=att.get('name', 'unknown'),
                contentType=att.get('contentType', 'application/octet-stream'),
                size=att.get('size', 0),
                contentBytes=att.get('contentBytes', '')
            ))
except Exception as att_error:
    print(f"⚠️ Lỗi khi lấy attachments: {att_error}")
    # Tiếp tục xử lý email dù không lấy được attachments

# Thêm attachments vào document
document = ParsedDocumentInfo(
    # ... các field khác ...
    attachments=attachments
)
```

---

## 🛡️ Security & Performance

### Giới hạn Size

- Microsoft Graph API giới hạn attachment: **< 3MB per file**
- Nếu file > 3MB, cần dùng uploadSession API (chưa implement)
- Nên validate size trước khi process

### Performance

- Mỗi email cần 1 API call để lấy attachments
- Với nhiều email, có thể mất thời gian
- Consider: Cache hoặc background job cho production

### Base64 Size

- Base64 encoded size ≈ 133% của original size
- JSON response có thể lớn nếu nhiều attachments
- Nên limit số lượng email fetch trong 1 lần

---

## 📊 Response Size Estimate

| Original File Size | Base64 Size | JSON Response Size |
|-------------------|-------------|-------------------|
| 100 KB            | ~133 KB     | ~135 KB           |
| 500 KB            | ~665 KB     | ~670 KB           |
| 1 MB              | ~1.33 MB    | ~1.35 MB          |
| 3 MB              | ~4 MB       | ~4.05 MB          |

**Khuyến nghị:** 
- Nên paginate nếu có > 10 emails
- Frontend nên có progress indicator khi fetch
- Consider upload trực tiếp lên storage thay vì qua API nếu file quá lớn

---

## 🆘 Troubleshooting

### ❌ Attachments luôn trả về []

**Nguyên nhân:**
- Email không có attachments
- Quyền Azure App chưa đủ (cần `Mail.Read`)
- Message ID không đúng

**Giải pháp:**
```bash
# Check logs trong console
docker-compose logs -f

# Hoặc khi chạy local
python main.py
```

### ❌ Lỗi decode base64 ở FE

**Nguyên nhân:**
- Base64 string bị truncate/corrupt
- Encoding không đúng

**Giải pháp:**
```javascript
// Validate base64 trước khi decode
function isValidBase64(str) {
  try {
    return btoa(atob(str)) === str;
  } catch (err) {
    return false;
  }
}
```

### ❌ Response quá lớn, timeout

**Nguyên nhân:**
- Quá nhiều email với attachments lớn

**Giải pháp:**
- Giảm `$top` parameter trong Graph API query
- Implement pagination
- Filter emails theo date range

---

## 📚 Tài liệu tham khảo

- [Microsoft Graph - Get Attachments](https://learn.microsoft.com/en-us/graph/api/message-list-attachments)
- [Base64 Encoding - MDN](https://developer.mozilla.org/en-US/docs/Glossary/Base64)
- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- **FE_ATTACHMENT_GUIDE.md** - Hướng dẫn chi tiết cho Frontend

---

## ✅ Checklist khi sử dụng

- [ ] Đã config Azure App permissions (`Mail.Read`, `Mail.ReadWrite`)
- [ ] API Key đã được set trong `.env`
- [ ] Đã test API với `test_receive_with_attachments.py`
- [ ] Frontend đã implement base64 decode
- [ ] Đã setup Supabase Storage bucket
- [ ] Đã test upload lên Supabase
- [ ] Đã handle error cases (no attachments, decode fail, upload fail)
- [ ] Đã implement progress indicator cho user

