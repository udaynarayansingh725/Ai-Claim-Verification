import json
from google import genai
from app.core.config import settings
from app.core.prompts import AI_DETECTION_PROMPT
from typing import Dict, Any
from app.core.logger import get_logger
from app.utils.gemini_client import generate_content_with_fallback
from app.services.heuristics import analyze_text_heuristics

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
    if not key_to_use or key_to_use.strip() in ["demo_key", "undefined", "null", "none", ""]:
        res = analyze_text_heuristics(text)
        return {
            "ai_probability": res["ai_probability"],
            "signals_detected": res["signals"],
            "confidence": "high" if (res["ai_probability"] > 0.65 or res["ai_probability"] < 0.35) else "medium"
        }
        
    client = genai.Client(api_key=key_to_use.strip())
    
    try:
        response = await generate_content_with_fallback(client, contents=prompt, preferred_model='gemini-2.0-flash')
        response_text = clean_json_response(response.text)
        result = json.loads(response_text)
        logger.info(f"AI detection complete. Probability: {result.get('ai_probability')}")
        return result
    except Exception as e:
        logger.warning(f"AI detection LLM failed, using heuristic fallback. Error: {str(e)}")
        res = analyze_text_heuristics(text)
        return {
            "ai_probability": res["ai_probability"],
            "signals_detected": res["signals"],
            "confidence": "high" if (res["ai_probability"] > 0.65 or res["ai_probability"] < 0.35) else "medium"
        }
