import json
import time
import base64
import asyncio
import traceback
from typing import Optional, Dict, Any
from google import genai
from app.services.text_detector import parse_confidence
from app.core.prompts import IMAGE_DETECTION_SYSTEM_PROMPT, IMAGE_DETECTION_USER_PROMPT
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.gemini_client import generate_content_sync_with_fallback
from app.services.heuristics import analyze_image_heuristics
from app.utils.validators import is_valid_api_key

logger = get_logger(__name__)

async def detect_image_content(image_bytes: bytes, api_key: Optional[str] = None) -> dict:
    start_time = time.time()
    logger.info("Starting AI image detection")
    
    # Sanitize and resolve API key
    key_to_use = api_key if is_valid_api_key(api_key) else settings.GEMINI_API_KEY
    if not is_valid_api_key(key_to_use):
        key_to_use = None
    else:
        key_to_use = key_to_use.strip()

    if not key_to_use:
        logger.info("No valid Gemini API key available; executing local heuristic image analysis")
        heuristic_res = analyze_image_heuristics(image_bytes)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }

    from app.utils.validators import get_mime_type
    mime = get_mime_type(image_bytes)
    
    try:
        client = genai.Client(api_key=key_to_use)
        system_prompt = IMAGE_DETECTION_SYSTEM_PROMPT
        user_prompt = IMAGE_DETECTION_USER_PROMPT

        def make_call():
            contents = [
                genai.types.Part.from_bytes(data=image_bytes, mime_type=mime),
                user_prompt
            ]
            config = genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                response_mime_type="application/json"
            )
            return generate_content_sync_with_fallback(client, contents=contents, config=config, preferred_model='gemini-2.0-flash')

        response = await asyncio.to_thread(make_call)
        data = json.loads(response.text)
        prob = float(data.get("ai_probability", 0.0))
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Image detection complete in {processing_time}ms: {prob} probability")
        return {
            "result": parse_confidence(prob),
            "confidence": prob,
            "signals": data.get("signals_detected", []),
            "processing_time_ms": processing_time
        }
    except Exception as e:
        logger.warning(f"Image detection LLM failed ({e}), falling back to local heuristic analysis")
        heuristic_res = analyze_image_heuristics(image_bytes)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }
