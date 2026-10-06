import json
import re
from google import genai
from app.core.config import settings
from app.core.prompts import CLAIM_EXTRACTION_PROMPT
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

async def extract_claims(text: str, api_key: str = None) -> list[str]:
    prompt = CLAIM_EXTRACTION_PROMPT.format(article_text=text)
    key_to_use = api_key or settings.GEMINI_API_KEY
    
    if not key_to_use:
        # Fallback if no key is configured
        if len(text.strip()) >= 5:
            return [text.strip()[:200]]
        return []

    client = genai.Client(api_key=key_to_use)
    
    try:
        response = await generate_content_with_fallback(client, contents=prompt, preferred_model='gemini-2.0-flash')
        response_text = clean_json_response(response.text)
        claims = json.loads(response_text)
        if not isinstance(claims, list):
            claims = [claims]
    except Exception as e:
        logger.warning(f"Claim extraction API failed ({str(e)}), attempting direct claim fallback...")
        if len(text.strip()) >= 5:
            return [text.strip()[:200]]
        raise RuntimeError(f"Claim extraction failed: {str(e)}")

    valid_claims = []
    for claim in claims:
        if isinstance(claim, str) and len(claim.strip()) >= 5:
            valid_claims.append(claim.strip())

    if not valid_claims and len(text.strip()) >= 5:
        valid_claims = [text.strip()[:200]]

    logger.info(f"Successfully extracted {len(valid_claims[:5])} valid claims")
    return valid_claims[:5]
