import json
import re
from app.core.config import settings
from app.core.prompts import CLAIM_EXTRACTION_PROMPT
from app.core.logger import get_logger
from app.utils.llm_client import generate_text_unified, clean_json_response, has_any_llm_key
from app.utils.validators import is_valid_api_key

logger = get_logger(__name__)

async def extract_claims(text: str, api_key: str = None) -> list[str]:
    prompt = CLAIM_EXTRACTION_PROMPT.format(article_text=text)
    
    if not has_any_llm_key(api_key):
        # Fallback if no valid key is configured
        if len(text.strip()) >= 5:
            return [text.strip()[:200]]
        return [text.strip()] if text.strip() else []

    try:
        raw_response = await generate_text_unified(prompt=prompt, api_key=api_key, json_mode=True)
        response_text = clean_json_response(raw_response)
        claims = json.loads(response_text)
        if not isinstance(claims, list):
            claims = [claims]
    except Exception as e:
        logger.warning(f"Claim extraction API failed ({str(e)}), attempting direct claim fallback...")
        if len(text.strip()) >= 5:
            return [text.strip()[:200]]
        return [text.strip()] if text.strip() else []

    valid_claims = []
    for claim in claims:
        if isinstance(claim, str) and len(claim.strip()) >= 5:
            valid_claims.append(claim.strip())

    if not valid_claims and len(text.strip()) >= 5:
        valid_claims = [text.strip()[:200]]

    logger.info(f"Successfully extracted {len(valid_claims[:5])} valid claims")
    return valid_claims[:5]
