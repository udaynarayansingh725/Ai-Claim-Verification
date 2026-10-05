import re
import trafilatura

URL_REGEX = re.compile(r'https?://[^\s]+')

def scrape_content(content: str) -> str:
    r"""
    Input detection logic:
    - Run regex to detect if content contains a valid URL (https?://\S+)
    - If URL found: extract URL, ignore surrounding text, scrape with trafilatura
    - If no URL: treat entire content as plain text
    """
    match = URL_REGEX.search(content)
    if match:
        url = match.group(0)
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            raise ValueError(f"Could not download URL: {url}")
        
        extracted_text = trafilatura.extract(
            downloaded, 
            include_comments=False, 
            include_tables=False
        )
        if not extracted_text or len(extracted_text) < 100:
            raise ValueError("Could not extract content from URL or text < 100 chars")
        return extracted_text
    else:
        # plain text
        return content

def is_url(content: str) -> bool:
    return bool(URL_REGEX.search(content))
