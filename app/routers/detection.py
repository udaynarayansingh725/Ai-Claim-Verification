from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import io
from PIL import Image

from app.schemas.api import DetectionResult, TextRequest
from app.utils.validators import validate_text, validate_image_file, validate_pdf_file
from app.services.text_detector import detect_text_content
from app.services.image_detector import detect_image_content
from app.services.pdf_detector import detect_pdf_content

router = APIRouter(prefix="/detect")

def get_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return x_api_key

@router.post("/text", response_model=DetectionResult)
async def detect_text(request: TextRequest, api_key: str = Depends(get_api_key)):
    valid_text = validate_text(request.text)
    result = await detect_text_content(valid_text, api_key)
    return result

@router.post("/image", response_model=DetectionResult)
async def detect_image(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    file_bytes = await validate_image_file(file)
    
    # Try opening with PIL to check corruption
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")
        
    result = await detect_image_content(file_bytes, api_key)
    return result

@router.post("/pdf", response_model=DetectionResult)
async def detect_pdf(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    file_bytes = await validate_pdf_file(file)
    result = await detect_pdf_content(file_bytes, api_key)
    return result
