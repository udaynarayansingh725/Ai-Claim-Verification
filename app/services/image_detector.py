import json
import time
import base64
import asyncio
import traceback
from typing import Dict, Any
from google import genai
from app.services.text_detector import parse_confidence
from app.core.prompts import IMAGE_DETECTION_SYSTEM_PROMPT, IMAGE_DETECTION_USER_PROMPT
from app.core.logger import get_logger
from app.utils.gemini_client import generate_content_sync_with_fallback

logger = get_logger(__name__)

async def detect_image_content(image_bytes: bytes, api_key: str) -> dict:
    start_time = time.time()
    logger.info("Starting AI image detection")
    client = genai.Client(api_key=api_key)
    
    system_prompt = IMAGE_DETECTION_SYSTEM_PROMPT
    user_prompt = IMAGE_DETECTION_USER_PROMPT

    from app.utils.validators import get_mime_type
    mime = get_mime_type(image_bytes)
    
    try:
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
        logger.error(f"Image detection failed: {e}\n{traceback.format_exc()}")
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": "uncertain",
            "confidence": 0.5,
            "signals": [f"Image detection unavailable: {str(e)[:100]}"],
            "processing_time_ms": processing_time
        }
