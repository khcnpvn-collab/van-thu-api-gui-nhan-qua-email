"""
FastAPI application cho email processor
"""
from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Header, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from graph_service import GraphService
from config import USER_EMAIL, API_KEY, generate_email_body, parse_email_body
import re
import json

app = FastAPI(
    title="Email Processor API",
    description="API để gửi và nhận email thông qua Microsoft Graph API",
    version="1.0.0"
)

# Khởi tạo Graph Service
graph_service = GraphService()

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency để verify API key từ header
    
    Args:
        api_key: API key từ header X-API-Key
        
    Returns:
        API key nếu hợp lệ
        
    Raises:
        HTTPException: Nếu API key không hợp lệ
    """
    if not API_KEY:
        # Nếu không config API_KEY trong .env, bỏ qua check (development mode)
        return None
        
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key


# Models cho request/response
class SendEmailRequest(BaseModel):
    """Model cho request gửi email"""
    mailTo: str
    subject: str
    body: str
    cc: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "mailTo": "abc@company.com",
                "subject": "Công văn đi",
                "body": "<p>Nội dung công văn...</p>",
                "cc": "manager@company.com"
            }
        }


class ParsedDocumentInfo(BaseModel):
    """Model cho thông tin document đã parse"""
    subject: str
    sentFrom: str
    docNumber: str
    docTime: str
    docSigner: str
    docPageNumber: str
    docPriority: str
    docKeyword: str
    docSecurity: str
    docId: str
    returnEmail: str
    messageId: str
    receivedDateTime: str


class IncomingDocumentsResponse(BaseModel):
    """Model cho response danh sách document đến"""
    length: int
    data: List[ParsedDocumentInfo]


def validate_email_body_format(body_content: str) -> tuple[bool, Optional[str]]:
    """
    Kiểm tra format của email body
    
    Args:
        body_content: Nội dung email cần kiểm tra
    
    Returns:
        Tuple (is_valid, message)
    """
    # Kiểm tra email body có chứa ít nhất 10 ký tự
    if not body_content or len(body_content.strip()) < 10:
        return False, "Email body quá ngắn (cần ít nhất 10 ký tự)"
    
    # Kiểm tra không phải là spam/rỗng
    spam_patterns = [
        r'^[\s\n\r]*$',  # Chỉ chứa whitespace
    ]
    
    for pattern in spam_patterns:
        if re.match(pattern, body_content):
            return False, "Email body không hợp lệ hoặc rỗng"
    
    return True, None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Email Processor API đang hoạt động",
        "version": "1.0.0"
    }


@app.post("/sendDocumentOutgoing", 
          summary="Gửi email công văn đi",
          description="API để gửi email với file đính kèm thông qua Microsoft Graph API")
async def send_document_outgoing(
    data: str = Form(..., description="JSON string chứa thông tin email: {mailTo, subject, information, cc}"),
    files: List[UploadFile] = File(None, description="Danh sách file đính kèm (optional)"),
    api_key: str = Security(verify_api_key)
):
    """
    Gửi email công văn đi với file đính kèm
    
    Args:
        data: JSON string chứa thông tin email (mailTo, subject, information, cc)
        files: Danh sách file đính kèm (optional)
    
    Returns:
        Thông tin kết quả gửi email
        
    Example data:
        {
            "mailTo": "recipient@example.com",
            "subject": "Công văn số 123",
            "information": {
                "docNumber": "123/CV",
                "docTime": "2024-01-15",
                "docSigner": "Nguyễn Văn A",
                "docPageNumber": "5",
                "docPriority": "Khẩn",
                "docKeyword": "Công văn",
                "docSecurity": "Thường",
                "docId": "CV-123",
                "returnEmail": "reply@example.com"
            },
            "cc": "manager@example.com"
        }
    """
    try:
        # Parse JSON từ form data
        try:
            email_data = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Dữ liệu JSON không hợp lệ trong field 'data'")
        
        # Validate các field bắt buộc
        if not email_data.get('mailTo'):
            raise HTTPException(status_code=400, detail="Field 'mailTo' là bắt buộc")
        if not email_data.get('subject'):
            raise HTTPException(status_code=400, detail="Field 'subject' là bắt buộc")
        if not email_data.get('information'):
            raise HTTPException(status_code=400, detail="Field 'information' là bắt buộc")
        
        # Validate information là dict
        if not isinstance(email_data.get('information'), dict):
            raise HTTPException(status_code=400, detail="Field 'information' phải là object/dict")
        
        # Parse danh sách email người nhận
        to_emails = [email.strip() for email in re.split('[,;]', email_data['mailTo']) if email.strip()]
        
        if not to_emails:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp email người nhận hợp lệ")
        
        # Parse danh sách email CC (nếu có và không rỗng)
        cc_emails = None
        cc_value = email_data.get('cc', '')
        if cc_value and str(cc_value).strip():
            cc_list = [email.strip() for email in re.split('[,;]', str(cc_value)) if email.strip()]
            if cc_list:
                cc_emails = cc_list
        
        # Tạo email body từ format template và information data
        # Body đã được escape HTML trong generate_email_body()
        email_body = generate_email_body(email_data['information'])
        
        # Wrap body trong <pre> tag để giữ format text
        # email_body đã được escape nên các tags <DOC>, <DOCNUMBER> sẽ hiển thị như text
        formatted_body = f"<pre style='font-family: Courier New, monospace; white-space: pre-wrap; font-size: 14px;'>{email_body}</pre>"
        
        # Xử lý files đính kèm
        attachments = []
        total_size = 0
        max_size = 25 * 1024 * 1024  # 25MB limit cho Graph API
        
        if files:
            for file in files:
                # Đọc nội dung file
                file_content = await file.read()
                file_size = len(file_content)
                total_size += file_size
                
                # Kiểm tra kích thước tổng
                if total_size > max_size:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Tổng kích thước file vượt quá giới hạn 25MB (hiện tại: {total_size / 1024 / 1024:.2f}MB)"
                    )
                
                attachments.append({
                    "filename": file.filename,
                    "content": file_content,
                    "content_type": file.content_type or "application/octet-stream"
                })
                
                # Reset file pointer để có thể đọc lại nếu cần
                await file.seek(0)
        
        # Gửi email với attachments
        result = graph_service.send_email(
            user_email=USER_EMAIL,
            to_recipients=to_emails,
            subject=email_data['subject'],
            body=formatted_body,
            cc_recipients=cc_emails,
            attachments=attachments if attachments else None
        )
        
        # Tạo response data
        response_data = {
            "from": USER_EMAIL,
            "to": to_emails,
            "subject": email_data['subject']
        }
        
        # Thêm cc vào response nếu có
        if cc_emails:
            response_data["cc"] = cc_emails
        
        # Thêm thông tin attachments vào response nếu có
        if attachments:
            response_data["attachments"] = [
                {
                    "filename": att["filename"],
                    "size": len(att["content"]),
                    "content_type": att["content_type"]
                } for att in attachments
            ]
            response_data["total_attachment_size"] = f"{total_size / 1024:.2f} KB"
        
        return {
            "success": True,
            "message": f"Email đã được gửi thành công{' với ' + str(len(attachments)) + ' file đính kèm' if attachments else ''}",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gửi email: {str(e)}")


@app.get("/receiveDocumentIncoming",
         response_model=IncomingDocumentsResponse,
         summary="Nhận email công văn đến",
         description="API để kiểm tra và lấy danh sách email chưa đọc có format hợp lệ")
async def receive_document_incoming(api_key: str = Security(verify_api_key)):
    """
    Nhận email công văn đến
    
    Lấy danh sách email chưa đọc từ hộp thư, parse body theo format template
    và trả về chỉ những email có format hợp lệ
    
    Sau khi parse thành công, email sẽ được đánh dấu là đã đọc
    
    Returns:
        Danh sách document đã parse với thông tin đầy đủ
    """
    try:
        # Lấy danh sách email chưa đọc
        unread_messages = graph_service.get_unread_messages(USER_EMAIL)
        
        # Parse và filter email có format hợp lệ
        parsed_documents = []
        marked_as_read_count = 0
        
        for message in unread_messages:
            message_id = message.get('id', '')
            
            # Lấy body content
            body_content = ""
            if message.get('body'):
                body_content = message['body'].get('content', '')
            
            # Parse body theo format template
            parsed_info = parse_email_body(body_content)
            
            # Chỉ xử lý email có format hợp lệ
            if parsed_info:
                # Lấy thông tin người gửi
                from_email = ""
                if message.get('from') and message['from'].get('emailAddress'):
                    from_email = message['from']['emailAddress'].get('address', '')
                
                # Tạo document info
                document = ParsedDocumentInfo(
                    subject=message.get('subject', ''),
                    sentFrom=from_email,
                    docNumber=parsed_info.get('docNumber', ''),
                    docTime=parsed_info.get('docTime', ''),
                    docSigner=parsed_info.get('docSigner', ''),
                    docPageNumber=parsed_info.get('docPageNumber', ''),
                    docPriority=parsed_info.get('docPriority', ''),
                    docKeyword=parsed_info.get('docKeyword', ''),
                    docSecurity=parsed_info.get('docSecurity', ''),
                    docId=parsed_info.get('docId', ''),
                    returnEmail=parsed_info.get('returnEmail', ''),
                    messageId=message_id,
                    receivedDateTime=message.get('receivedDateTime', '')
                )
                
                parsed_documents.append(document)
                
                # Đánh dấu email đã đọc sau khi parse thành công
                try:
                    if message_id:
                        print(f"🔄 Đang đánh dấu email {message_id[:30]}... đã đọc")
                        mark_success = graph_service.mark_as_read(USER_EMAIL, message_id)
                        if mark_success:
                            marked_as_read_count += 1
                            print(f"✅ Đã đánh dấu email {message_id[:30]}... đã đọc")
                        else:
                            print(f"❌ Không thể đánh dấu email {message_id[:30]}... (API trả về False)")
                except Exception as mark_error:
                    # Log error chi tiết
                    print(f"❌ Lỗi khi đánh dấu email {message_id[:30]}... đã đọc: {type(mark_error).__name__}: {mark_error}")
                    import traceback
                    traceback.print_exc()
        
        print(f"✅ Đã parse {len(parsed_documents)} email và đánh dấu {marked_as_read_count} email đã đọc")
        
        return IncomingDocumentsResponse(
            length=len(parsed_documents),
            data=parsed_documents
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy email: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

