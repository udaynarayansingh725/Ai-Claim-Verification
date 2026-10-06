import asyncio
import time
from google import genai
from app.core.logger import get_logger

logger = get_logger(__name__)

CANDIDATE_MODELS = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-3.8-flash']

async def generate_content_with_fallback(client: genai.Client, contents, config=None, preferred_model: str = None):
    models_to_try = list(CANDIDATE_MODELS)
    if preferred_model and preferred_model in models_to_try:
        models_to_try.remove(preferred_model)
        models_to_try.insert(0, preferred_model)
    elif preferred_model:
        models_to_try.insert(0, preferred_model)

    last_exception = None

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                logger.debug(f"Attempting Gemini generate_content with model '{model_name}' (attempt {attempt+1})")
                kwargs = {"model": model_name, "contents": contents}
                if config:
                    kwargs["config"] = config
                
                response = await client.aio.models.generate_content(**kwargs)
                return response
            except Exception as e:
                err_str = str(e)
                last_exception = e
                # Check for 503 UNAVAILABLE or 429 RESOURCE_EXHAUSTED or high demand
                if any(k in err_str for k in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "high demand"]):
                    logger.warning(f"Gemini API model '{model_name}' high demand/unavailable ({err_str[:100]}...). Retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.warning(f"Gemini API model '{model_name}' returned error: {err_str[:100]}. Trying next model...")
                    break

    logger.error(f"All Gemini candidate models failed. Last error: {str(last_exception)}")
    raise last_exception


def generate_content_sync_with_fallback(client: genai.Client, contents, config=None, preferred_model: str = None):
    models_to_try = list(CANDIDATE_MODELS)
    if preferred_model and preferred_model in models_to_try:
        models_to_try.remove(preferred_model)
        models_to_try.insert(0, preferred_model)
    elif preferred_model:
        models_to_try.insert(0, preferred_model)

    last_exception = None

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                kwargs = {"model": model_name, "contents": contents}
                if config:
                    kwargs["config"] = config
                
                response = client.models.generate_content(**kwargs)
                return response
            except Exception as e:
                err_str = str(e)
                last_exception = e
                if any(k in err_str for k in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "high demand"]):
                    time.sleep(1)
                    continue
                else:
                    break

    raise last_exception
