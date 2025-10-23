# 📎 Hướng dẫn xử lý Attachments từ API cho Frontend

## 📥 API Response Structure

Khi gọi API `GET /receiveDocumentIncoming`, response sẽ có cấu trúc:

```json
{
  "length": 1,
  "data": [
    {
      "subject": "Công văn số 123",
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
      "messageId": "AAMkAGE...",
      "receivedDateTime": "2024-01-15T10:30:00Z",
      "attachments": [
        {
          "name": "document.pdf",
          "contentType": "application/pdf",
          "size": 524288,
          "contentBytes": "JVBERi0xLjQKJeLjz9MKM..."  // Base64 encoded
        },
        {
          "name": "image.jpg",
          "contentType": "image/jpeg",
          "size": 153600,
          "contentBytes": "/9j/4AAQSkZJRgABAQEASA..."  // Base64 encoded
        }
      ]
    }
  ]
}
```

---

## 🔧 Xử lý Attachments trong Frontend

### 1️⃣ **JavaScript/TypeScript - Convert Base64 sang Blob**

```javascript
// Hàm convert base64 sang Blob
function base64ToBlob(base64String, contentType) {
  const byteCharacters = atob(base64String);
  const byteNumbers = new Array(byteCharacters.length);
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: contentType });
}

// Hàm convert base64 sang File object
function base64ToFile(base64String, filename, contentType) {
  const blob = base64ToBlob(base64String, contentType);
  return new File([blob], filename, { type: contentType });
}

// Sử dụng
const attachment = document.attachments[0];
const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
const file = base64ToFile(
  attachment.contentBytes, 
  attachment.name, 
  attachment.contentType
);
```

---

### 2️⃣ **Upload lên Supabase Storage**

#### Cách 1: Upload trực tiếp từ Base64

```javascript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function uploadAttachmentToSupabase(attachment, bucketName, folderPath = '') {
  try {
    // Convert base64 sang Blob
    const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
    
    // Tạo file path (có thể thêm folder path)
    const filePath = folderPath 
      ? `${folderPath}/${attachment.name}` 
      : attachment.name;
    
    // Upload lên Supabase Storage
    const { data, error } = await supabase.storage
      .from(bucketName)
      .upload(filePath, blob, {
        contentType: attachment.contentType,
        upsert: false  // hoặc true nếu muốn overwrite
      });
    
    if (error) {
      throw error;
    }
    
    console.log('✅ Upload thành công:', data);
    
    // Lấy public URL (nếu bucket là public)
    const { data: urlData } = supabase.storage
      .from(bucketName)
      .getPublicUrl(filePath);
    
    return {
      success: true,
      path: data.path,
      publicUrl: urlData.publicUrl
    };
    
  } catch (error) {
    console.error('❌ Upload failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Sử dụng
const result = await uploadAttachmentToSupabase(
  attachment,
  'documents',  // bucket name
  'incoming-docs/2024-01'  // folder path (optional)
);
```

#### Cách 2: Upload File object (tương tự upload file từ input)

```javascript
async function uploadFileToSupabase(attachment, bucketName, folderPath = '') {
  try {
    // Convert base64 sang File object
    const file = base64ToFile(
      attachment.contentBytes, 
      attachment.name, 
      attachment.contentType
    );
    
    const filePath = folderPath ? `${folderPath}/${file.name}` : file.name;
    
    // Upload như file bình thường
    const { data, error } = await supabase.storage
      .from(bucketName)
      .upload(filePath, file);
    
    if (error) throw error;
    
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

---

### 3️⃣ **Upload nhiều attachments cùng lúc**

```javascript
async function uploadAllAttachments(documents, bucketName) {
  const results = [];
  
  for (const doc of documents) {
    // Tạo folder theo docId
    const folderPath = `documents/${doc.docId}`;
    
    for (const attachment of doc.attachments) {
      const result = await uploadAttachmentToSupabase(
        attachment,
        bucketName,
        folderPath
      );
      
      results.push({
        docId: doc.docId,
        fileName: attachment.name,
        ...result
      });
    }
  }
  
  return results;
}

// Sử dụng
const apiResponse = await fetch('/receiveDocumentIncoming', {
  headers: { 'X-API-Key': 'your-api-key' }
});

const { data: documents } = await apiResponse.json();

// Upload tất cả attachments
const uploadResults = await uploadAllAttachments(documents, 'documents');
console.log('Upload results:', uploadResults);
```

---

### 4️⃣ **Download file từ attachment**

```javascript
// Tạo download link cho user
function downloadAttachment(attachment) {
  const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
  const url = URL.createObjectURL(blob);
  
  // Tạo thẻ <a> để download
  const a = document.createElement('a');
  a.href = url;
  a.download = attachment.name;
  document.body.appendChild(a);
  a.click();
  
  // Cleanup
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Sử dụng
document.getElementById('downloadBtn').addEventListener('click', () => {
  downloadAttachment(attachment);
});
```

---

### 5️⃣ **Preview file (image, PDF)**

#### Preview Image

```javascript
function previewImage(attachment) {
  if (!attachment.contentType.startsWith('image/')) {
    console.error('Không phải file image');
    return;
  }
  
  const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
  const url = URL.createObjectURL(blob);
  
  // Hiển thị trong img tag
  const img = document.getElementById('previewImage');
  img.src = url;
  img.alt = attachment.name;
  
  // Nhớ cleanup khi không cần nữa
  img.onload = () => URL.revokeObjectURL(url);
}
```

#### Preview PDF (trong iframe)

```javascript
function previewPDF(attachment) {
  if (attachment.contentType !== 'application/pdf') {
    console.error('Không phải file PDF');
    return;
  }
  
  const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
  const url = URL.createObjectURL(blob);
  
  // Hiển thị trong iframe
  const iframe = document.getElementById('pdfViewer');
  iframe.src = url;
}
```

---

## ⚛️ React Example

### Hook để xử lý attachments

```typescript
import { useState } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

interface Attachment {
  name: string;
  contentType: string;
  size: number;
  contentBytes: string;
}

export function useAttachmentUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const base64ToBlob = (base64: string, contentType: string): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  };
  
  const uploadToSupabase = async (
    attachment: Attachment,
    bucketName: string,
    path: string
  ) => {
    setUploading(true);
    
    try {
      const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);
      
      const { data, error } = await supabase.storage
        .from(bucketName)
        .upload(`${path}/${attachment.name}`, blob, {
          contentType: attachment.contentType
        });
      
      if (error) throw error;
      
      // Lấy public URL
      const { data: urlData } = supabase.storage
        .from(bucketName)
        .getPublicUrl(`${path}/${attachment.name}`);
      
      setProgress(100);
      setUploading(false);
      
      return { success: true, url: urlData.publicUrl };
    } catch (error) {
      setUploading(false);
      return { success: false, error };
    }
  };
  
  return { uploadToSupabase, uploading, progress };
}
```

### Component sử dụng

```typescript
import { useAttachmentUpload } from './hooks/useAttachmentUpload';

function DocumentViewer({ document }) {
  const { uploadToSupabase, uploading } = useAttachmentUpload();
  
  const handleUploadAll = async () => {
    for (const attachment of document.attachments) {
      const result = await uploadToSupabase(
        attachment,
        'documents',
        `docs/${document.docId}`
      );
      
      if (result.success) {
        console.log(`✅ ${attachment.name} uploaded:`, result.url);
      } else {
        console.error(`❌ ${attachment.name} failed:`, result.error);
      }
    }
  };
  
  return (
    <div>
      <h3>{document.subject}</h3>
      <div>
        <h4>Attachments ({document.attachments.length})</h4>
        <ul>
          {document.attachments.map((att, idx) => (
            <li key={idx}>
              {att.name} - {(att.size / 1024).toFixed(2)} KB
            </li>
          ))}
        </ul>
        <button onClick={handleUploadAll} disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload All to Supabase'}
        </button>
      </div>
    </div>
  );
}
```

---

## 🎯 Best Practices

### 1. **Xử lý file lớn**

```javascript
// Kiểm tra size trước khi upload
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

function validateAttachment(attachment) {
  if (attachment.size > MAX_SIZE) {
    alert(`File ${attachment.name} quá lớn (max 10MB)`);
    return false;
  }
  return true;
}
```

### 2. **Rename file để tránh conflict**

```javascript
function generateUniqueFileName(originalName) {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  const extension = originalName.split('.').pop();
  const nameWithoutExt = originalName.replace(`.${extension}`, '');
  
  return `${nameWithoutExt}_${timestamp}_${random}.${extension}`;
}

// Upload với tên unique
const uniqueName = generateUniqueFileName(attachment.name);
const blob = base64ToBlob(attachment.contentBytes, attachment.contentType);

await supabase.storage
  .from('documents')
  .upload(`docs/${uniqueName}`, blob);
```

### 3. **Retry logic khi upload fail**

```javascript
async function uploadWithRetry(attachment, maxRetries = 3) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await uploadAttachmentToSupabase(attachment, 'documents');
      if (result.success) return result;
    } catch (error) {
      lastError = error;
      console.log(`Retry ${i + 1}/${maxRetries}...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  
  throw lastError;
}
```

### 4. **Batch upload với progress tracking**

```javascript
async function batchUpload(attachments, onProgress) {
  const total = attachments.length;
  let completed = 0;
  
  for (const attachment of attachments) {
    await uploadAttachmentToSupabase(attachment, 'documents');
    completed++;
    onProgress(Math.round((completed / total) * 100));
  }
}

// Sử dụng
await batchUpload(document.attachments, (progress) => {
  console.log(`Upload progress: ${progress}%`);
  document.getElementById('progressBar').value = progress;
});
```

---

## 📚 Resources

- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- [MDN - Base64 encoding and decoding](https://developer.mozilla.org/en-US/docs/Glossary/Base64)
- [File API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/File)

---

## 🆘 Troubleshooting

### ❌ Lỗi: "Invalid base64 string"

**Nguyên nhân:** Base64 string bị corrupt hoặc không đúng format

**Giải pháp:**
```javascript
// Validate base64 string trước khi decode
function isValidBase64(str) {
  try {
    return btoa(atob(str)) === str;
  } catch (err) {
    return false;
  }
}

if (!isValidBase64(attachment.contentBytes)) {
  console.error('Invalid base64 string');
}
```

### ❌ Lỗi: "Blob/File size is 0"

**Nguyên nhân:** Decode base64 không thành công

**Giải pháp:**
```javascript
// Thêm padding nếu thiếu
function fixBase64Padding(base64) {
  const padding = base64.length % 4;
  if (padding > 0) {
    return base64 + '='.repeat(4 - padding);
  }
  return base64;
}

const fixedBase64 = fixBase64Padding(attachment.contentBytes);
```

### ❌ Lỗi Supabase: "Storage exceeded quota"

**Giải pháp:** Kiểm tra quota của bucket, clean up old files, hoặc upgrade plan

