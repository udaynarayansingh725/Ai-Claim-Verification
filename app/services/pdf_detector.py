import json
import time
import io
import asyncio
from typing import Optional, Dict, Any
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from fastapi import HTTPException
from pdf2image import convert_from_bytes
from app.services.text_detector import parse_confidence
from app.services.image_detector import detect_image_content
from app.core.prompts import PDF_DETECTION_SYSTEM_PROMPT, PDF_DETECTION_USER_PROMPT
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.llm_client import generate_text_unified, clean_json_response, has_any_llm_key
from app.services.heuristics import analyze_text_heuristics

logger = get_logger(__name__)

async def detect_pdf_content(pdf_bytes: bytes, api_key: Optional[str] = None) -> dict:
    start_time = time.time()
    logger.info("Starting AI pdf detection")
    
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
            
            return await detect_image_content(img_bytes, api_key)
        except Exception as e:
            logger.error(f"PDF-to-image conversion failed: {e}")
            raise HTTPException(status_code=422, detail="Could not read file. It may be corrupted.")

    extracted_text = extracted_text[:8000]

    if not has_any_llm_key(api_key):
        logger.info("No Gemini or OpenAI API key available; executing local heuristic statistical analysis on PDF text")
        heuristic_res = analyze_text_heuristics(extracted_text)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }

    try:
        user_prompt = PDF_DETECTION_USER_PROMPT.format(text=extracted_text)
        raw_response = await generate_text_unified(
            prompt=user_prompt,
            system_prompt=PDF_DETECTION_SYSTEM_PROMPT,
            api_key=api_key,
            json_mode=True
        )
        response_text = clean_json_response(raw_response)
        data = json.loads(response_text)
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
