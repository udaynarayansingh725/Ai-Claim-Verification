import re
from fastapi import UploadFile, HTTPException

def is_valid_api_key(key: str | None) -> bool:
    if not key:
        return False
    k = key.strip()
    if len(k) < 15:
        return False
    lower_k = k.lower()
    if any(placeholder in lower_k for placeholder in [
        "your_gemini_api_key", "your_openai_api_key", "your_api_key", "your_tavily_api_key",
        "demo_key", "placeholder", "undefined", "null", "none", "insert"
    ]):
        return False
    return True

def is_openai_key(key: str | None) -> bool:
    if not is_valid_api_key(key):
        return False
    k = key.strip()
    return k.startswith("sk-") or "openai" in k.lower()

def is_gemini_key(key: str | None) -> bool:
    if not is_valid_api_key(key):
        return False
    return not is_openai_key(key)

def get_mime_type(content: bytes) -> str:
    if content.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif content.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif content.startswith(b'RIFF') and b'WEBP' in content[8:12]:
        return 'image/webp'
    elif content.startswith(b'%PDF-'):
        return 'application/pdf'
    return 'application/octet-stream'

def validate_text(text: str) -> str:
    text = text.strip()
    if len(text) < 100:
        raise HTTPException(status_code=422, detail="Text too short. Minimum 100 characters required.")
    if len(text) > 10000:
        raise HTTPException(status_code=422, detail="Text too long. Maximum 10,000 characters allowed.")
        
    # Check if > 80% numeric/special characters
    alphanumeric_chars = len(re.findall(r'[a-zA-Z]', text))
    if alphanumeric_chars / len(text) < 0.2:
        raise HTTPException(status_code=422, detail="Text format invalid. Contains > 80% numeric or special characters.")
        
    return text

async def validate_image_file(file: UploadFile) -> bytes:
    content = await file.read()
    await file.seek(0)
    
    if len(content) < 10 * 1024:
        raise HTTPException(status_code=422, detail="File too small. Minimum size is 10KB.")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File too large. Maximum size is 5MB.")
        
    mime = get_mime_type(content)
    allowed_mimes = ['image/jpeg', 'image/png', 'image/webp']
    if mime not in allowed_mimes:
        raise HTTPException(status_code=422, detail="Invalid file type. Allowed: JPEG, PNG, WEBP.")
    
    return content

async def validate_pdf_file(file: UploadFile) -> bytes:
    content = await file.read()
    await file.seek(0)
    
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File too large. Maximum size is 5MB.")
        
    mime = get_mime_type(content)
    if mime != 'application/pdf':
        raise HTTPException(status_code=422, detail="Invalid file type. Must be a PDF.")
        
    return content
