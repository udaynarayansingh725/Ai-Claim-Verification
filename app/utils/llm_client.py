import json
import base64
import asyncio
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.core.logger import get_logger
from app.utils.validators import is_valid_api_key, is_openai_key, is_gemini_key
from app.utils.gemini_client import generate_content_with_fallback

logger = get_logger(__name__)

OPENAI_MODELS = ['gpt-4o-mini', 'gpt-4o']

def clean_json_response(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def has_any_llm_key(api_key: Optional[str] = None) -> bool:
    if is_valid_api_key(api_key):
        return True
    if is_valid_api_key(settings.GEMINI_API_KEY):
        return True
    if is_valid_api_key(settings.OPENAI_API_KEY):
        return True
    return False

# ==========================================
# OpenAI Implementations
# ==========================================
async def call_openai_text(prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None, json_mode: bool = False) -> str:
    from openai import AsyncOpenAI
    key = api_key or settings.OPENAI_API_KEY
    if not is_valid_api_key(key):
        raise ValueError("No valid OpenAI API key available")
        
    client = AsyncOpenAI(api_key=key.strip())
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for model_name in OPENAI_MODELS:
        try:
            kwargs: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.1,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            logger.debug(f"Calling OpenAI model '{model_name}'...")
            resp = await client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or ""
            return content
        except Exception as e:
            logger.warning(f"OpenAI model '{model_name}' failed: {e}")
            last_error = e

    raise last_error or RuntimeError("OpenAI call failed across all candidate models")

async def call_openai_vision(image_bytes: bytes, mime_type: str, user_prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None, json_mode: bool = False) -> str:
    from openai import AsyncOpenAI
    key = api_key or settings.OPENAI_API_KEY
    if not is_valid_api_key(key):
        raise ValueError("No valid OpenAI API key available")
        
    client = AsyncOpenAI(api_key=key.strip())
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:{mime_type};base64,{b64_image}"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]
    })

    last_error = None
    for model_name in OPENAI_MODELS:
        try:
            kwargs: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.1,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            logger.debug(f"Calling OpenAI vision model '{model_name}'...")
            resp = await client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"OpenAI vision model '{model_name}' failed: {e}")
            last_error = e

    raise last_error or RuntimeError("OpenAI vision call failed")

# ==========================================
# Gemini Implementations
# ==========================================
async def call_gemini_text(prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None, json_mode: bool = False) -> str:
    from google import genai
    key = api_key or settings.GEMINI_API_KEY
    if not is_valid_api_key(key):
        raise ValueError("No valid Gemini API key available")
        
    client = genai.Client(api_key=key.strip())
    config = None
    if system_prompt or json_mode:
        cfg_args: Dict[str, Any] = {"temperature": 0.1}
        if system_prompt:
            cfg_args["system_instruction"] = system_prompt
        if json_mode:
            cfg_args["response_mime_type"] = "application/json"
        config = genai.types.GenerateContentConfig(**cfg_args)

    resp = await generate_content_with_fallback(client, contents=prompt, config=config, preferred_model='gemini-2.0-flash')
    return resp.text or ""

async def call_gemini_vision(image_bytes: bytes, mime_type: str, user_prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None, json_mode: bool = False) -> str:
    from google import genai
    key = api_key or settings.GEMINI_API_KEY
    if not is_valid_api_key(key):
        raise ValueError("No valid Gemini API key available")

    client = genai.Client(api_key=key.strip())
    contents = [
        genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        user_prompt
    ]
    cfg_args: Dict[str, Any] = {"temperature": 0.1}
    if system_prompt:
        cfg_args["system_instruction"] = system_prompt
    if json_mode:
        cfg_args["response_mime_type"] = "application/json"
    config = genai.types.GenerateContentConfig(**cfg_args)

    resp = await generate_content_with_fallback(client, contents=contents, config=config, preferred_model='gemini-2.0-flash')
    return resp.text or ""

# ==========================================
# Master Unified Fallback Dispatachers
# ==========================================
async def generate_text_unified(
    prompt: str, 
    system_prompt: Optional[str] = None, 
    api_key: Optional[str] = None, 
    json_mode: bool = False
) -> str:
    """
    Executes text generation using available provider:
    1. If a specific valid API key is passed:
       - Uses OpenAI if key is an OpenAI key (sk-...)
       - Uses Gemini if key is a Gemini key
    2. If no valid key passed in call:
       - Checks configured server keys (GEMINI_API_KEY, OPENAI_API_KEY)
       - Automatically tries Gemini first, falls back to OpenAI on failure (or vice versa)
    """
    clean_key = api_key.strip() if is_valid_api_key(api_key) else None

    # Case 1: User explicitly provided a key
    if clean_key:
        if is_openai_key(clean_key):
            logger.info("Using OpenAI with user-provided API key")
            return await call_openai_text(prompt, system_prompt, clean_key, json_mode)
        else:
            logger.info("Using Gemini with user-provided API key")
            return await call_gemini_text(prompt, system_prompt, clean_key, json_mode)

    # Case 2: Use environment/server keys
    has_gemini = is_valid_api_key(settings.GEMINI_API_KEY)
    has_openai = is_valid_api_key(settings.OPENAI_API_KEY)

    if not has_gemini and not has_openai:
        raise ValueError("No valid Gemini or OpenAI API key configured")

    last_error = None

    # If Gemini configured, try it
    if has_gemini:
        try:
            return await call_gemini_text(prompt, system_prompt, settings.GEMINI_API_KEY.strip(), json_mode)
        except Exception as e:
            logger.warning(f"Gemini call failed: {e}. Checking for OpenAI fallback...")
            last_error = e

    # Fallback to OpenAI if configured
    if has_openai:
        try:
            logger.info("Activating OpenAI fallback for text generation")
            return await call_openai_text(prompt, system_prompt, settings.OPENAI_API_KEY.strip(), json_mode)
        except Exception as e:
            logger.warning(f"OpenAI fallback call failed: {e}")
            last_error = e

    raise last_error or RuntimeError("All LLM providers failed")

async def generate_vision_unified(
    image_bytes: bytes,
    mime_type: str,
    user_prompt: str,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    json_mode: bool = False
) -> str:
    """
    Executes multimodal vision analysis using available provider with fallback.
    """
    clean_key = api_key.strip() if is_valid_api_key(api_key) else None

    if clean_key:
        if is_openai_key(clean_key):
            logger.info("Using OpenAI vision with user-provided API key")
            return await call_openai_vision(image_bytes, mime_type, user_prompt, system_prompt, clean_key, json_mode)
        else:
            logger.info("Using Gemini vision with user-provided API key")
            return await call_gemini_vision(image_bytes, mime_type, user_prompt, system_prompt, clean_key, json_mode)

    has_gemini = is_valid_api_key(settings.GEMINI_API_KEY)
    has_openai = is_valid_api_key(settings.OPENAI_API_KEY)

    if not has_gemini and not has_openai:
        raise ValueError("No valid Gemini or OpenAI API key configured")

    last_error = None

    if has_gemini:
        try:
            return await call_gemini_vision(image_bytes, mime_type, user_prompt, system_prompt, settings.GEMINI_API_KEY.strip(), json_mode)
        except Exception as e:
            logger.warning(f"Gemini vision call failed: {e}. Checking for OpenAI fallback...")
            last_error = e

    if has_openai:
        try:
            logger.info("Activating OpenAI fallback for vision analysis")
            return await call_openai_vision(image_bytes, mime_type, user_prompt, system_prompt, settings.OPENAI_API_KEY.strip(), json_mode)
        except Exception as e:
            logger.warning(f"OpenAI vision call failed: {e}")
            last_error = e

    raise last_error or RuntimeError("All vision providers failed")
