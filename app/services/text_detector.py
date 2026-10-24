import json
import time
import asyncio
from typing import Optional, Dict, Any
from app.core.prompts import TEXT_DETECTION_SYSTEM_PROMPT, TEXT_DETECTION_USER_PROMPT
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.llm_client import generate_text_unified, clean_json_response, has_any_llm_key
from app.services.heuristics import analyze_text_heuristics

logger = get_logger(__name__)

def parse_confidence(prob: float) -> str:
    if prob <= 0.35:
        return "human_written"
    elif prob <= 0.64:
        return "uncertain"
    return "ai_generated"

async def detect_text_content(text: str, api_key: Optional[str] = None) -> dict:
    start_time = time.time()
    logger.info("Starting AI text detection")
    
    if not has_any_llm_key(api_key):
        logger.info("No valid Gemini or OpenAI API key available; executing local heuristic statistical analysis")
        heuristic_res = analyze_text_heuristics(text)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "sentence_scores": heuristic_res.get("sentence_scores", []),
            "processing_time_ms": processing_time
        }

    try:
        user_prompt = TEXT_DETECTION_USER_PROMPT.format(text=text)
        raw_response = await generate_text_unified(
            prompt=user_prompt,
            system_prompt=TEXT_DETECTION_SYSTEM_PROMPT,
            api_key=api_key,
            json_mode=True
        )
        response_text = clean_json_response(raw_response)
        data = json.loads(response_text)
        prob = float(data.get("ai_probability", 0.0))
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Text detection complete in {processing_time}ms: {prob} probability")
        
        # Sentence scores generator for LLM results
        raw_sentences = [s.strip() for s in text.splitlines() if s.strip()] or [text]
        sentence_scores = [{"text": s, "ai_probability": prob, "is_ai": prob >= 0.65} for s in raw_sentences]

        return {
            "result": parse_confidence(prob),
            "confidence": prob,
            "signals": data.get("signals_detected", []),
            "sentence_scores": sentence_scores,
            "processing_time_ms": processing_time
        }
    except Exception as e:
        logger.warning(f"Text detection LLM failed ({e}), falling back to local heuristic analysis")
        heuristic_res = analyze_text_heuristics(text)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "result": heuristic_res["result"],
            "confidence": heuristic_res["ai_probability"],
            "signals": heuristic_res["signals"],
            "sentence_scores": heuristic_res.get("sentence_scores", []),
            "processing_time_ms": processing_time
        }
