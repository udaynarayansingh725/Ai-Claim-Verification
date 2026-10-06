import json
import re
from urllib.parse import urlparse
from google import genai
from typing import List, Dict, Any
from app.core.prompts import VERIFICATION_PROMPT, SELF_REFLECTION_PROMPT
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.gemini_client import generate_content_with_fallback

logger = get_logger(__name__)

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "with", "by", "about", "against",
    "between", "into", "through", "during", "before", "after", "above",
    "below", "from", "up", "down", "of", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "should", "now", "what",
    "which", "who", "whom", "this", "that", "these", "those"
}

NEGATION_TERMS = {"false", "fake", "hoax", "myth", "debunked", "refuted", "untrue", "incorrect", "misleading", "fabricated", "disproven"}
CONFIRMATION_TERMS = {"true", "verified", "fact", "confirmed", "indeed", "proven", "accurate", "authentic"}

def heuristic_verify_claim(claim: str, sources: List[Dict[str, str]]) -> Dict[str, Any]:
    words = re.findall(r'\b[a-zA-Z0-9]+\b', claim.lower())
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    if not keywords or not sources:
        return {
            "verdict": "Unverifiable",
            "confidence": 0.5,
            "reasoning": "Insufficient web search evidence available to evaluate this claim.",
            "conflicting_sources": False
        }

    combined_text = " ".join(
        f"{src.get('title', '')} {src.get('snippet', '')}".lower()
        for src in sources
    )

    matched_keywords = [kw for kw in keywords if kw in combined_text]
    match_ratio = len(matched_keywords) / len(keywords) if keywords else 0

    neg_matches = sum(1 for term in NEGATION_TERMS if term in combined_text)
    pos_matches = sum(1 for term in CONFIRMATION_TERMS if term in combined_text)

    top_domain = ""
    if sources:
        top_url = sources[0].get("url", "")
        if top_url:
            top_domain = urlparse(top_url).netloc

    source_count = len(sources)
    domain_text = f" ({top_domain})" if top_domain else ""

    if match_ratio >= 0.5:
        if neg_matches > pos_matches and neg_matches >= 1:
            verdict = "False"
            confidence = 0.85
            reasoning = f"Web search evidence from {source_count} source(s){domain_text} refutes or debunks this claim."
            conflicting = False
        elif neg_matches > 0 and pos_matches > 0:
            verdict = "Partially True"
            confidence = 0.70
            reasoning = f"Web search evidence from {source_count} source(s){domain_text} contains mixed context regarding this claim."
            conflicting = True
        else:
            verdict = "True"
            confidence = 0.88
            reasoning = f"Web search evidence from {source_count} source(s){domain_text} supports and confirms this claim."
            conflicting = False
    elif match_ratio >= 0.3:
        verdict = "Partially True"
        confidence = 0.65
        reasoning = f"Partial web search evidence from {source_count} source(s){domain_text} aligns with this claim."
        conflicting = False
    else:
        verdict = "Unverifiable"
        confidence = 0.50
        reasoning = f"Web search results do not contain conclusive evidence to verify or refute this claim."
        conflicting = False

    return {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "conflicting_sources": conflicting
    }

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
    if not key_to_use:
        return {"verdict": "Unverifiable", "confidence": 0.5, "reasoning": "No API key configured", "conflicting_sources": False}

    client = genai.Client(api_key=key_to_use)
    response = await generate_content_with_fallback(client, contents=prompt, preferred_model='gemini-2.0-flash')
    text = clean_json_response(response.text)
    return json.loads(text)

async def verify_claim(claim: str, sources: List[Dict[str, str]], api_key: str = None) -> Dict[str, Any]:
    evidence_block = build_evidence_block(sources)
    prompt = VERIFICATION_PROMPT.format(claim=claim, evidence_block=evidence_block)
    
    try:
        result = await _verify_with_prompt(prompt, api_key)
    except Exception as e:
        logger.warning(f"Verification LLM failed ({str(e)}), invoking heuristic search evidence fallback...")
        return heuristic_verify_claim(claim, sources)
        
    confidence = result.get("confidence", 0.0)
    verdict = result.get("verdict", "Unverifiable")
    
    if confidence < 0.6 and verdict != "Unverifiable":
        logger.debug(f"Low confidence ({confidence}) for verdict {verdict}. Triggering reflection.")
        reflection_prompt = prompt + "\n\n" + SELF_REFLECTION_PROMPT.format(verdict=verdict, confidence=confidence)
        try:
            result = await _verify_with_prompt(reflection_prompt, api_key)
        except Exception as e:
            logger.error(f"Reflection prompt failed, using base result: {str(e)}")
            pass
            
    verdict = result.get("verdict", "Unverifiable")
    conflicting = result.get("conflicting_sources", False)
    
    if conflicting and verdict == "True":
        result["verdict"] = "Partially True"
        
    logger.info(f"Final verdict for claim '{claim[:30]}...': {result.get('verdict')} (Confidence: {result.get('confidence', 0.0)})")
    return result
