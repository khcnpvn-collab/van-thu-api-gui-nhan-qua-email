"""
Service layer để tương tác với Microsoft Graph API
"""
import msal
import requests
import base64
import time
from typing import Dict, List, Optional
from config import CLIENT_ID, TENANT_ID, CLIENT_SECRET, GRAPH_API_ENDPOINT, AUTHORITY, SCOPE


class GraphService:
    """Service để tương tác với Microsoft Graph API"""
    
    def __init__(self):
        self.client_id = CLIENT_ID
        self.tenant_id = TENANT_ID
        self.client_secret = CLIENT_SECRET
        self.authority = AUTHORITY
        self.scope = SCOPE
        self.access_token = None
        self.token_expiry = 0  # Timestamp khi token hết hạn (5 phút)
    
    def get_access_token(self) -> str:
        """
        Lấy access token với caching 5 phút
        - Lần đầu: Request token mới
        - Sau đó: Reuse token trong 5 phút
        - Sau 5 phút: Request token mới
        """
        current_time = time.time()
        
        # Kiểm tra xem token còn valid không (trong vòng 5 phút)
        if self.access_token and current_time < self.token_expiry:
            remaining_seconds = int(self.token_expiry - current_time)
            print(f"🔄 Reuse token (còn {remaining_seconds}s)")
            return self.access_token
        
        # Token hết hạn hoặc chưa có token → lấy mới
        print("🔑 Lấy access token mới...")
        
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            # Set expire sau 5 phút (300 giây)
            self.token_expiry = current_time + 300
            print(f"✅ Token mới - valid trong 5 phút")
            return self.access_token
        else:
            error_msg = result.get('error_description', 'Unknown error')
            raise Exception(f"Không thể lấy access token: {error_msg}")
    
    def send_email(self, user_email: str, to_recipients: List[str], subject: str, 
                   body: str, cc_recipients: Optional[List[str]] = None,
                   attachments: Optional[List[Dict]] = None) -> Dict:
        """
        Gửi email qua Graph API với file đính kèm
        
        Args:
            user_email: Email người gửi
            to_recipients: Danh sách email người nhận
            subject: Tiêu đề email
            body: Nội dung email
            cc_recipients: Danh sách email CC
            attachments: Danh sách file đính kèm
                        [{"filename": "file.pdf", "content": bytes, "content_type": "application/pdf"}]
        """
        token = self.get_access_token()
        
        # Chuẩn bị danh sách người nhận
        to_list = [{"emailAddress": {"address": email}} for email in to_recipients]
        
        # Chuẩn bị message
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": to_list
            }
        }
        
        # Thêm CC nếu có và không rỗng
        if cc_recipients and len(cc_recipients) > 0:
            cc_list = [{"emailAddress": {"address": email}} for email in cc_recipients]
            message["message"]["ccRecipients"] = cc_list
        
        # Thêm attachments nếu có
        if attachments and len(attachments) > 0:
            attachment_list = []
            for att in attachments:
                # Encode file content thành base64
                content_bytes = att["content"]
                content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                
                attachment_list.append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att["filename"],
                    "contentType": att["content_type"],
                    "contentBytes": content_base64
                })
            
            message["message"]["attachments"] = attachment_list
        
        # Gửi request
        endpoint = f"{GRAPH_API_ENDPOINT}/users/{user_email}/sendMail"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(endpoint, headers=headers, json=message)
        
        if response.status_code == 202:
            attachment_count = len(attachments) if attachments else 0
            return {
                "status": "success", 
                "message": f"Email đã được gửi thành công{' với ' + str(attachment_count) + ' file đính kèm' if attachment_count > 0 else ''}"
            }
        else:
            raise Exception(f"Lỗi khi gửi email: {response.status_code} - {response.text}")
    
    def get_unread_messages(self, user_email: str) -> List[Dict]:
        """
        Lấy danh sách email chưa đọc từ hộp thư
        
        Args:
            user_email: Email cần kiểm tra
        """
        token = self.get_access_token()
        
        # Query để lấy email chưa đọc
        endpoint = f"{GRAPH_API_ENDPOINT}/users/{user_email}/messages"
        params = {
            '$filter': 'isRead eq false',
            '$select': 'id,subject,from,receivedDateTime,bodyPreview,body',
            '$top': 50,
            '$orderby': 'receivedDateTime DESC'
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('value', [])
        else:
            raise Exception(f"Lỗi khi lấy email: {response.status_code} - {response.text}")
    
    def mark_as_read(self, user_email: str, message_id: str) -> bool:
        """
        Đánh dấu email đã đọc
        
        Args:
            user_email: Email người dùng
            message_id: ID của message cần đánh dấu
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        token = self.get_access_token()
        
        endpoint = f"{GRAPH_API_ENDPOINT}/users/{user_email}/messages/{message_id}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        data = {"isRead": True}
        
        response = requests.patch(endpoint, headers=headers, json=data)
        
        # Graph API trả về 200 OK hoặc 204 No Content khi thành công
        if response.status_code in [200, 204]:
            return True
        else:
            # Log lỗi để debug
            print(f"⚠️ Mark as read failed: Status {response.status_code}, Response: {response.text[:200]}")
            return False
    
    def _make_request_with_retry(self, method: str, endpoint: str, headers: Dict, 
                                  max_retries: int = 3, **kwargs) -> requests.Response:
        """
        HTTP request với retry cho rate limit/errors
        
        Retry với exponential backoff: 1s → 2s → 4s
        """
        for attempt in range(max_retries):
            try:
                response = requests.request(method, endpoint, headers=headers, **kwargs)
                
                # Nếu gặp 429 (rate limit) hoặc 503 (service unavailable), retry
                if response.status_code in [429, 503] and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    print(f"⚠️ Error {response.status_code}, retry sau {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ Request error: {e}, retry sau {wait_time}s")
                    time.sleep(wait_time)
                    continue
                raise
        
        return response
    
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
        
        response = self._make_request_with_retry('GET', endpoint, headers)
        
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
            print(f"⚠️ Get attachments failed: Status {response.status_code}, Response: {response.text[:200]}")
            return []

