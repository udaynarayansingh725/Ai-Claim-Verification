import json
import time
import asyncio
import traceback
from google import genai
from typing import Dict, Any
from app.core.prompts import TEXT_DETECTION_SYSTEM_PROMPT, TEXT_DETECTION_USER_PROMPT
from app.core.logger import get_logger

logger = get_logger(__name__)

def parse_confidence(prob: float) -> str:
    if prob <= 0.35:
        return "human_written"
    elif prob <= 0.64:
        return "uncertain"
    return "ai_generated"

async def detect_text_content(text: str, api_key: str) -> dict:
    start_time = time.time()
    logger.info("Starting AI text detection")
    client = genai.Client(api_key=api_key)
    
    system_prompt = TEXT_DETECTION_SYSTEM_PROMPT
    user_prompt = TEXT_DETECTION_USER_PROMPT.format(text=text)

    for attempt in range(3):
        try:
            logger.debug(f"Calling Gemini API (attempt {attempt+1}/3)")
            def make_call():
                return client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[user_prompt],
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )

            response = await asyncio.to_thread(make_call)
            
            data = json.loads(response.text)
            prob = float(data.get("ai_probability", 0.0))
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Text detection complete in {processing_time}ms: {prob} probability")
            return {
                "result": parse_confidence(prob),
                "confidence": prob,
                "signals": data.get("signals_detected", []),
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Gemini API error (text, attempt {attempt+1}): {e}\n{traceback.format_exc()}")
            if attempt == 2:
                break
            await asyncio.sleep(1)

    logger.warning("Text detection failed after 3 attempts")
    processing_time = int((time.time() - start_time) * 1000)
    return {
        "result": "uncertain",
        "confidence": 0.5,
        "signals": ["detection unavailable, please retry"],
        "processing_time_ms": processing_time
    }
