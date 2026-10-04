"""URL verification service: fetches web article body text and extracts main claims."""
import urllib.request
import urllib.parse
import re
from .claim_service import verify_claim


def fetch_url_content(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    
    # Strip script and style tags
    clean_html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", clean_html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def verify_url_article(url: str) -> dict:
    try:
        content = fetch_url_content(url)
        if len(content) < 50:
            return {"verdict": "NOT ENOUGH INFO", "confidence": 0.0, "signals": ["Could not extract readable text from URL."]}
            
        # Extract main claim (first 300 characters or key sentence)
        sentences = re.split(r"(?<=[.!?])\s+", content)
        main_claim = " ".join(sentences[:2]) if len(sentences) >= 2 else content[:300]
        
        result = verify_claim(main_claim)
        result["extracted_claim"] = main_claim
        result["url"] = url
        return result
    except Exception as e:
        return {
            "verdict": "ERROR",
            "confidence": 0.0,
            "signals": [f"Failed to fetch or parse URL: {str(e)}"],
            "url": url
        }
