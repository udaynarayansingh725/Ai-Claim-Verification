import asyncio
from typing import List, Dict, Any, Tuple
from tavily import AsyncTavilyClient
from duckduckgo_search import DDGS
from app.core.config import settings
from app.core.prompts import SEARCH_QUERY_PROMPT
from google import genai
from urllib.parse import urlparse
from app.core.logger import get_logger

logger = get_logger(__name__)

tavily_client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY or "dummy_key")
search_semaphore = asyncio.Semaphore(3)

AUTHORITATIVE_DOMAINS = ["wikipedia.org", "reuters.com", "bbc.com", "apnews.com", ".gov", ".edu"]

def is_authoritative(url: str) -> bool:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    for auth in AUTHORITATIVE_DOMAINS:
        if domain.endswith(auth):
            return True
    return False

async def generate_query(claim: str, api_key: str = None) -> str:
    prompt = SEARCH_QUERY_PROMPT.format(claim=claim)
    key_to_use = api_key or settings.GEMINI_API_KEY
    client = genai.Client(api_key=key_to_use)
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        query = response.text.strip()
        logger.debug(f"Generated search query: '{query}' for claim: '{claim[:50]}...'")
        return query
    except Exception as e:
        logger.error(f"Failed to generate query, using claim as fallback. Error: {str(e)}")
        return claim[:60]

async def tavily_search(query: str) -> List[Dict[str, Any]]:
    try:
        logger.info(f"Executing Tavily search for: '{query}'")
        response = await tavily_client.search(
            query=query, 
            search_depth="basic", 
            max_results=3,
            include_answer=False,
            include_raw_content=False
        )
        results = response.get("results", [])
        
        for result in results:
            if result.get("score", 0) > 0.8 and is_authoritative(result.get("url", "")):
                try:
                    extract_response = await tavily_client.extract(urls=[result["url"]])
                    extract_results = extract_response.get("results", [])
                    if extract_results:
                        raw_content = extract_results[0].get("raw_content", "")
                        if raw_content:
                            result["content"] = raw_content[:1500]
                except Exception:
                    pass
        return results
    except Exception as e:
        if "429" in str(e):
            logger.warning("Tavily rate limit hit. Sleeping and retrying...")
            await asyncio.sleep(2)
            try:
                response = await tavily_client.search(query=query, search_depth="basic", max_results=3)
                return response.get("results", [])
            except Exception:
                pass
        logger.error(f"Tavily search failed entirely: {str(e)}")
        raise RuntimeError("Tavily failed")

async def duckduckgo_search(query: str) -> List[Dict[str, Any]]:
    logger.info(f"Executing DuckDuckGo fallback search for: '{query}'")
    try:
        def do_search():
            results = []
            ddgs = DDGS()
            for r in ddgs.text(query, max_results=3):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "content": r.get("body", ""),
                    "score": 0.5
                })
            return results
        return await asyncio.to_thread(do_search)
    except Exception:
        return []

async def search_for_claim(claim: str, api_key: str = None) -> Tuple[str, List[Dict[str, str]]]:
    async with search_semaphore:
        query = await generate_query(claim, api_key)
        
        try:
            results = await tavily_search(query)
        except Exception:
            logger.warning("Primary search engine failed, invoking DuckDuckGo.")
            results = await duckduckgo_search(query)
            
        if not results:
            logger.warning("No results from primary source, invoking DuckDuckGo.")
            results = await duckduckgo_search(query)

        logger.info(f"Found {len(results)} results total for claim")
        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")
            })
        return query, formatted
