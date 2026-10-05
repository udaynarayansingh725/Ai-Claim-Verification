import json
import re
from google import genai
from app.core.config import settings
from app.core.prompts import CLAIM_EXTRACTION_PROMPT
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

async def extract_claims(text: str, api_key: str = None) -> list[str]:
    prompt = CLAIM_EXTRACTION_PROMPT.format(article_text=text)
    key_to_use = api_key or settings.GEMINI_API_KEY
    client = genai.Client(api_key=key_to_use)
    
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
    except Exception as e:
        logger.error(f"Claim extraction API failed: {str(e)}")
        raise RuntimeError(f"Claim extraction failed: {str(e)}")
        
    response_text = clean_json_response(response.text)
    
    try:
        claims = json.loads(response_text)
        if not isinstance(claims, list):
            claims = [claims]
    except json.JSONDecodeError:
        # Retry once
        try:
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
            response_text = clean_json_response(response.text)
            claims = json.loads(response_text)
            if not isinstance(claims, list):
                claims = [claims]
        except Exception as e:
            logger.error(f"Failed to parse claims JSON after retry: {str(e)}")
            raise RuntimeError(f"Failed to parse claims JSON: {str(e)}")

    valid_claims = []
    for claim in claims:
        if isinstance(claim, str) and len(claim) >= 10:
            valid_claims.append(claim)
            
    logger.info(f"Successfully extracted {len(valid_claims[:5])} valid claims")
    return valid_claims[:5] # Maximum 5 claims
