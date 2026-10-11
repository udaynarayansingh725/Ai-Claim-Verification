import json
import time
import io
import asyncio
import traceback
from typing import Optional, Dict, Any
from google import genai
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from fastapi import HTTPException
from pdf2image import convert_from_bytes
from app.services.text_detector import parse_confidence
from app.services.image_detector import detect_image_content
from app.core.prompts import PDF_DETECTION_SYSTEM_PROMPT, PDF_DETECTION_USER_PROMPT
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.gemini_client import generate_content_sync_with_fallback
from app.services.heuristics import analyze_text_heuristics
from app.utils.validators import is_valid_api_key

logger = get_logger(__name__)

async def detect_pdf_content(pdf_bytes: bytes, api_key: Optional[str] = None) -> dict:
    start_time = time.time()
    logger.info("Starting AI pdf detection")
    
    # Sanitize and resolve API key
    key_to_use = api_key if is_valid_api_key(api_key) else settings.GEMINI_API_KEY
    if not is_valid_api_key(key_to_use):
        key_to_use = None
    else:
        key_to_use = key_to_use.strip()
    
    try:
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        
        if reader.is_encrypted:
            logger.warning("PDF is password protected")
            raise HTTPException(status_code=422, detail="PDF is password protected.")
            
        num_pages = len(reader.pages)
        if num_pages == 0:
            logger.warning("Empty PDF file")
            raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")
        if num_pages > 10:
            logger.warning(f"PDF too long: {num_pages} pages")
            raise HTTPException(status_code=422, detail="PDF exceeds maximum page limit of 10 pages.")
        
        extracted_text = ""
        for i in range(num_pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                extracted_text += page_text + "\n"
                
        extracted_text = extracted_text.strip()
        
    except PdfReadError as e:
        logger.error(f"Failed to read PDF file: {e}")
        raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Unexpected error determining PDF content: {e}")
        raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")
        
    if not extracted_text:
        logger.info("No text extracted from PDF. Falling back to image detection for the first page.")
        try:
            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
            if not images:
                raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")
            
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            return await detect_image_content(img_bytes, key_to_use)
        except Exception as e:
            logger.error(f"PDF-to-image conversion failed: {e}")
            raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")

    extracted_text = extracted_text[:8000]

    if not key_to_use:
        logger.info("No Gemini API key available; executing local heuristic statistical analysis on PDF text")
        heuristic_res = analyze_text_heuristics(extracted_text)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }

    try:
        client = genai.Client(api_key=key_to_use)
        system_prompt = PDF_DETECTION_SYSTEM_PROMPT
        user_prompt = PDF_DETECTION_USER_PROMPT.format(text=extracted_text)

        def make_call():
            config = genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                response_mime_type="application/json"
            )
            return generate_content_sync_with_fallback(client, contents=[user_prompt], config=config, preferred_model='gemini-2.0-flash')

        response = await asyncio.to_thread(make_call)
        data = json.loads(response.text)
        prob = float(data.get("ai_probability", 0.0))
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"PDF detection complete in {processing_time}ms: {prob} probability")
        return {
            "result": parse_confidence(prob),
            "confidence": prob,
            "signals": data.get("signals_detected", []),
            "processing_time_ms": processing_time
        }
    except Exception as e:
        logger.warning(f"PDF detection LLM failed ({e}), falling back to local heuristic analysis")
        heuristic_res = analyze_text_heuristics(extracted_text)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }
