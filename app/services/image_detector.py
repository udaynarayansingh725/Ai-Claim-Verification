import json
import time
import asyncio
from typing import Optional, Dict, Any
from app.services.text_detector import parse_confidence
from app.core.prompts import IMAGE_DETECTION_SYSTEM_PROMPT, IMAGE_DETECTION_USER_PROMPT
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.llm_client import generate_vision_unified, clean_json_response, has_any_llm_key
from app.services.heuristics import analyze_image_heuristics
from app.utils.validators import get_mime_type

logger = get_logger(__name__)

async def detect_image_content(image_bytes: bytes, api_key: Optional[str] = None, filename: str = "") -> dict:
    start_time = time.time()
    logger.info("Starting AI image detection")
    
    if not has_any_llm_key(api_key):
        logger.info("No valid Gemini or OpenAI API key available; executing local heuristic image analysis")
        heuristic_res = analyze_image_heuristics(image_bytes, filename=filename)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }

    mime = get_mime_type(image_bytes)
    
    try:
        raw_response = await generate_vision_unified(
            image_bytes=image_bytes,
            mime_type=mime,
            user_prompt=IMAGE_DETECTION_USER_PROMPT,
            system_prompt=IMAGE_DETECTION_SYSTEM_PROMPT,
            api_key=api_key,
            json_mode=True
        )
        response_text = clean_json_response(raw_response)
        data = json.loads(response_text)
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
        heuristic_res = analyze_image_heuristics(image_bytes, filename=filename)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "processing_time_ms": processing_time
        }
