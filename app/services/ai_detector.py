import json
from app.core.config import settings
from app.core.prompts import AI_DETECTION_PROMPT
from typing import Dict, Any
from app.core.logger import get_logger
from app.utils.llm_client import generate_text_unified, clean_json_response, has_any_llm_key
from app.services.heuristics import analyze_text_heuristics

logger = get_logger(__name__)

async def detect_ai(text: str, api_key: str = None) -> Dict[str, Any]:
    prompt = AI_DETECTION_PROMPT.format(text=text[:3000])
    
    if not has_any_llm_key(api_key):
        res = analyze_text_heuristics(text)
        return {
            "ai_probability": res["ai_probability"],
            "signals_detected": res["signals"],
            "confidence": "high" if (res["ai_probability"] > 0.65 or res["ai_probability"] < 0.35) else "medium"
        }

    try:
        raw_response = await generate_text_unified(prompt=prompt, api_key=api_key, json_mode=True)
        response_text = clean_json_response(raw_response)
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
