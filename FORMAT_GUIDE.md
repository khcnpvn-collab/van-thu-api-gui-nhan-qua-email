# Hướng dẫn Format Template Email

## 📋 Giới thiệu

API sử dụng format template được định nghĩa trong file `info.txt` để tự động tạo nội dung email. Format này đảm bảo tất cả email công văn đều có cấu trúc thống nhất.

## 📝 Format Template

Format template được định nghĩa trong file **`email_format.txt`** (file riêng biệt):

```xml
<DOC>
<DOCNUMBER>{docNumber}</DOCNUMBER>
<DOCTIME>{docTime}</DOCTIME>
<DOCSIGNER>{docSigner}</DOCSIGNER>
<DOCPAGENUMBER>{docPageNumber}</DOCPAGENUMBER>
<DOCPRIORITY>{docPriority}</DOCPRIORITY>
<DOCKEYWORD>{docKeyword}</DOCKEYWORD>
<DOCSECURITY>{docSecurity}</DOCSECURITY>
<DOCID>{docId}</DOCID>
<RETURN-EMAIL>{returnEmail}</RETURN-EMAIL>
</DOC>
```

## 🔄 Cách hoạt động

1. **Load Template**: Khi server khởi động, format template được đọc từ file `info.txt`
2. **Nhận Request**: API nhận JSON với field `information` chứa dữ liệu công văn
3. **Replace Placeholder**: Các placeholder `{docNumber}`, `{docTime}`,... được thay thế bằng giá trị thực tế
4. **Generate Body**: Body email được tạo và gửi đi với format đã định

## 📥 Cấu trúc Request

```json
{
  "mailTo": "recipient@example.com",
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
  "cc": "manager@example.com"
}
```

## 📤 Email được tạo ra

Email người nhận sẽ thấy:

```xml
<DOC>
<DOCNUMBER>123/CV-2024</DOCNUMBER>
<DOCTIME>15/01/2024 10:30</DOCTIME>
<DOCSIGNER>Nguyễn Văn A - Giám đốc</DOCSIGNER>
<DOCPAGENUMBER>5</DOCPAGENUMBER>
<DOCPRIORITY>Khẩn</DOCPRIORITY>
<DOCKEYWORD>Công văn, Báo cáo</DOCKEYWORD>
<DOCSECURITY>Thường</DOCSECURITY>
<DOCID>CV-2024-123</DOCID>
<RETURN-EMAIL>reply@company.com</RETURN-EMAIL>
</DOC>
```

## 🔧 Các Placeholder

| Placeholder | Mô tả | Ví dụ |
|------------|-------|-------|
| `{docNumber}` | Số công văn | `123/CV-2024` |
| `{docTime}` | Thời gian công văn | `15/01/2024 10:30` |
| `{docSigner}` | Người ký | `Nguyễn Văn A - Giám đốc` |
| `{docPageNumber}` | Số trang | `5` |
| `{docPriority}` | Độ ưu tiên | `Khẩn`, `Thường`, `Hỏa tốc` |
| `{docKeyword}` | Từ khóa | `Công văn, Báo cáo` |
| `{docSecurity}` | Độ mật | `Thường`, `Mật`, `Tối mật` |
| `{docId}` | Mã công văn | `CV-2024-123` |
| `{returnEmail}` | Email phản hồi | `reply@company.com` |

## ⚙️ Cấu hình Format

Để thay đổi format template:

1. Mở file `email_format.txt`
2. Chỉnh sửa format theo ý muốn
3. Lưu file (đảm bảo UTF-8 encoding)
4. Restart server: `bash run.sh`

**Ví dụ custom format (trong file `email_format.txt`):**

```xml
============ CÔNG VĂN ============
Số: {docNumber}
Ngày: {docTime}
Người ký: {docSigner}
Số trang: {docPageNumber}
Độ ưu tiên: {docPriority}
Từ khóa: {docKeyword}
Phân loại: {docSecurity}
Mã số: {docId}
Email liên hệ: {returnEmail}
==================================
```

Hoặc giữ nguyên format XML:

```xml
<DOC>
<DOCNUMBER>{docNumber}</DOCNUMBER>
<DOCTIME>{docTime}</DOCTIME>
<DOCSIGNER>{docSigner}</DOCSIGNER>
<DOCPAGENUMBER>{docPageNumber}</DOCPAGENUMBER>
<DOCPRIORITY>{docPriority}</DOCPRIORITY>
<DOCKEYWORD>{docKeyword}</DOCKEYWORD>
<DOCSECURITY>{docSecurity}</DOCSECURITY>
<DOCID>{docId}</DOCID>
<RETURN-EMAIL>{returnEmail}</RETURN-EMAIL>
</DOC>
```

## 🎨 Hiển thị trong Email

Email body được xử lý như sau:

1. **Escape HTML**: Các ký tự `<` và `>` được chuyển thành `&lt;` và `&gt;`
   - Điều này đảm bảo tags như `<DOC>`, `<DOCNUMBER>` hiển thị như TEXT thay vì bị parse như HTML
   
2. **Wrap trong `<pre>` tag**: Với font monospace để giữ nguyên format

```html
<pre style='font-family: Courier New, monospace; white-space: pre-wrap; font-size: 14px;'>
&lt;DOC&gt;
&lt;DOCNUMBER&gt;123/CV-2024&lt;/DOCNUMBER&gt;
...
&lt;/DOC&gt;
</pre>
```

**Kết quả người nhận sẽ thấy:**

```
<DOC>
<DOCNUMBER>123/CV-2024</DOCNUMBER>
<DOCTIME>15/01/2024</DOCTIME>
...
</DOC>
```

Điều này đảm bảo:
- ✅ Hiển thị tags như text (không bị ẩn)
- ✅ Giữ nguyên line breaks
- ✅ Giữ nguyên indentation
- ✅ Font dễ đọc
- ✅ Hiển thị đúng trên mọi email client

## 🧪 Test Format

Chạy script test để xem format hoạt động:

```bash
source venv/bin/activate
python test_new_format.py
```

Script này sẽ:
1. Hiển thị format template từ file
2. Generate email body mẫu
3. Test gửi email với format thực tế

## 📌 Lưu ý

1. **Không bỏ trống**: Nếu field nào không có giá trị, truyền chuỗi rỗng `""` thay vì bỏ field
2. **Encoding**: File `info.txt` phải được lưu với UTF-8 encoding để hỗ trợ tiếng Việt
3. **Restart required**: Sau khi thay đổi format trong `info.txt`, cần restart server
4. **Placeholder chính xác**: Placeholder phải khớp chính xác (case-sensitive)

## 🔍 Troubleshooting

### Placeholder không được thay thế

**Nguyên nhân**: Tên placeholder không khớp

**Giải pháp**: Kiểm tra lại spelling trong `info.txt` và request JSON

### Format bị lỗi khi hiển thị

**Nguyên nhân**: Email client không hỗ trợ `<pre>` tag

**Giải pháp**: Đã được xử lý bằng inline style, nên hiển thị tốt trên hầu hết email client

### Tiếng Việt bị lỗi

**Nguyên nhân**: File `email_format.txt` không phải UTF-8

**Giải pháp**: Mở file bằng editor và save as UTF-8

### Tags không hiển thị

**Nguyên nhân**: Trước đây tags bị parse như HTML

**Giải pháp**: Đã fix bằng `html.escape()` - tags giờ hiển thị như text

