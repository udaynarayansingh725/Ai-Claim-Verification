import json
from google import genai
from typing import List, Dict, Any
from app.core.prompts import VERIFICATION_PROMPT, SELF_REFLECTION_PROMPT
from app.core.config import settings
from app.core.logger import get_logger

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

def build_evidence_block(sources: List[Dict[str, str]]) -> str:
    parts = []
    for i, src in enumerate(sources[:5], start=1):
        title = src.get("title", "")
        url = src.get("url", "")
        content = src.get("snippet", "")[:400]
        parts.append(f"[Source {i}] {title}\nURL: {url}\nExcerpt: {content}\n")
    return "\n".join(parts)

async def _verify_with_prompt(prompt: str, api_key: str = None) -> Dict[str, Any]:
    key_to_use = api_key or settings.GEMINI_API_KEY
    client = genai.Client(api_key=key_to_use)
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = clean_json_response(response.text)
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Initial verification generation failed, retrying... Error: {str(e)}")
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = clean_json_response(response.text)
        return json.loads(text)

async def verify_claim(claim: str, sources: List[Dict[str, str]], api_key: str = None) -> Dict[str, Any]:
    evidence_block = build_evidence_block(sources)
    prompt = VERIFICATION_PROMPT.format(claim=claim, evidence_block=evidence_block)
    
    try:
        result = await _verify_with_prompt(prompt, api_key)
    except Exception as e:
        logger.error(f"Verification pipeline failed completely: {str(e)}")
        raise RuntimeError(f"Verification failed: {str(e)}")
        
    confidence = result.get("confidence", 0.0)
    verdict = result.get("verdict", "Unverifiable")
    
    if confidence < 0.6 and verdict != "Unverifiable":
        logger.debug(f"Low confidence ({confidence}) for verdict {verdict}. Triggering reflection.")
        reflection_prompt = prompt + "\n\n" + SELF_REFLECTION_PROMPT.format(verdict=verdict, confidence=confidence)
        try:
            result = await _verify_with_prompt(reflection_prompt, api_key)
        except Exception as e:
            logger.error(f"Reflection prompt failed, using base result: {str(e)}")
            pass # fallback to first result
            
    verdict = result.get("verdict", "Unverifiable")
    conflicting = result.get("conflicting_sources", False)
    
    if conflicting and verdict == "True":
        result["verdict"] = "Partially True"
        
    logger.info(f"Final verdict for claim '{claim[:30]}...': {result.get('verdict')} (Confidence: {result.get('confidence', 0.0)})")
    return result
