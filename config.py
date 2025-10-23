"""
Module cấu hình cho ứng dụng email processor
"""
import os
import html
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables từ .env file
load_dotenv()

# Load credentials từ environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
TENANT_ID = os.getenv('TENANT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USER_EMAIL = os.getenv('USER_EMAIL')
API_KEY = os.getenv('API_KEY')

# Load email format từ file
def load_email_format():
    """Load email format template từ file"""
    format_file = Path(__file__).parent / "email_format.txt"
    if format_file.exists():
        with open(format_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

EMAIL_FORMAT = load_email_format()

# Microsoft Graph API endpoints
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPE = ['https://graph.microsoft.com/.default']


def generate_email_body(information: dict) -> str:
    """
    Tạo email body từ format template và information data
    
    Args:
        information: Dict chứa các field docNumber, docTime, docSigner, v.v.
    
    Returns:
        Email body đã được format và escape HTML
    """
    body = EMAIL_FORMAT
    
    # Replace các placeholder với giá trị thực tế
    replacements = {
        '{docNumber}': str(information.get('docNumber', '')),
        '{docTime}': str(information.get('docTime', '')),
        '{docSigner}': str(information.get('docSigner', '')),
        '{docPageNumber}': str(information.get('docPageNumber', '')),
        '{docPriority}': str(information.get('docPriority', '')),
        '{docKeyword}': str(information.get('docKeyword', '')),
        '{docSecurity}': str(information.get('docSecurity', '')),
        '{docId}': str(information.get('docId', '')),
        '{returnEmail}': str(information.get('returnEmail', ''))
    }
    
    for placeholder, value in replacements.items():
        body = body.replace(placeholder, value)
    
    # Escape HTML để hiển thị tags như text thay vì parse như HTML
    # Chuyển < thành &lt; và > thành &gt;
    body = html.escape(body)
    
    return body


def parse_email_body(body_content: str) -> dict:
    """
    Parse email body để extract thông tin theo format template
    
    Args:
        body_content: Nội dung email body (HTML hoặc text)
    
    Returns:
        Dict chứa thông tin đã parse, hoặc None nếu không match format
    """
    import re
    
    # Unescape HTML nếu có (chuyển &lt; thành <, &gt; thành >)
    body_text = html.unescape(body_content)
    
    # QUAN TRỌNG: KHÔNG remove tất cả HTML tags vì sẽ mất <DOC>, <DOCNUMBER>
    # Chỉ loại bỏ các HTML tags CỤ THỂ, giữ lại XML tags
    # Remove common HTML tags: html, head, body, pre, div, span, p, meta, style
    html_tags_to_remove = [
        r'<html[^>]*>',
        r'</html>',
        r'<head[^>]*>',
        r'</head>',
        r'<body[^>]*>',
        r'</body>',
        r'<pre[^>]*>',
        r'</pre>',
        r'<div[^>]*>',
        r'</div>',
        r'<span[^>]*>',
        r'</span>',
        r'<p[^>]*>',
        r'</p>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'\\r',
        r'\\n'
    ]
    
    for pattern in html_tags_to_remove:
        body_text = re.sub(pattern, '', body_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Kiểm tra có chứa <DOC> không
    if '<DOC>' not in body_text or '</DOC>' not in body_text:
        return None
    
    # Parse từng field
    result = {}
    
    # Định nghĩa các pattern để extract
    patterns = {
        'docNumber': r'<DOCNUMBER>(.*?)</DOCNUMBER>',
        'docTime': r'<DOCTIME>(.*?)</DOCTIME>',
        'docSigner': r'<DOCSIGNER>(.*?)</DOCSIGNER>',
        'docPageNumber': r'<DOCPAGENUMBER>(.*?)</DOCPAGENUMBER>',
        'docPriority': r'<DOCPRIORITY>(.*?)</DOCPRIORITY>',
        'docKeyword': r'<DOCKEYWORD>(.*?)</DOCKEYWORD>',
        'docSecurity': r'<DOCSECURITY>(.*?)</DOCSECURITY>',
        'docId': r'<DOCID>(.*?)</DOCID>',
        'returnEmail': r'<RETURN-EMAIL>(.*?)</RETURN-EMAIL>'
    }
    
    # Extract từng field
    for field, pattern in patterns.items():
        match = re.search(pattern, body_text, re.DOTALL | re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()
        else:
            # Nếu thiếu field bắt buộc, return None
            return None
    
    # Kiểm tra ít nhất phải có docNumber
    if not result.get('docNumber'):
        return None
    
    return result

