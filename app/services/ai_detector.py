import json
from google import genai
from app.core.config import settings
from app.core.prompts import AI_DETECTION_PROMPT
from typing import Dict, Any
from app.core.logger import get_logger
from app.utils.gemini_client import generate_content_with_fallback

logger = get_logger(__name__)

def clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def detect_ai(text: str, api_key: str = None) -> Dict[str, Any]:
    prompt = AI_DETECTION_PROMPT.format(text=text[:3000])
    key_to_use = api_key or settings.GEMINI_API_KEY
    if not key_to_use:
        return {"ai_probability": 0.0, "signals_detected": ["No API key provided"], "confidence": "low"}
        
    client = genai.Client(api_key=key_to_use)
    
    try:
        response = await generate_content_with_fallback(client, contents=prompt, preferred_model='gemini-2.0-flash')
        response_text = clean_json_response(response.text)
        result = json.loads(response_text)
        logger.info(f"AI detection complete. Probability: {result.get('ai_probability')}")
        return result
    except Exception as e:
        logger.error(f"AI detection failed, using fallback. Error: {str(e)}")
        return {"ai_probability": 0.0, "signals_detected": [], "confidence": "high"}
