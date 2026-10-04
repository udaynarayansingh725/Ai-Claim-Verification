"""Claim verification: claim -> keywords -> evidence search -> stance detection -> cross-verification -> verdict.

Features:
  - Multilingual & Hinglish keyword extraction
  - Evidence stance classification (AGREES, DISAGREES, NEUTRAL)
  - Pluggable evidence provider (NewsAPI or Builtin Pool)
"""
import re
import urllib.parse
import urllib.request
import json
from ..config import NEWSAPI_KEY, SUPPORT_THRESHOLD, REFUTE_CUE_BONUS, MAX_EVIDENCE

STOPWORDS = {
    "a","an","the","is","are","was","were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","shall","can","must","need","dare","ought","used",
    "to","of","in","for","on","with","at","by","from","as","into","through","during","before","after",
    "above","below","between","out","off","over","under","again","further","then","once","here","there",
    "when","where","why","how","all","any","both","each","few","more","most","other","some","such",
    "no","nor","not","only","own","same","so","than","too","very","just","and","but","if","or","because",
    "while","that","this","these","those","it","its","he","she","they","them","his","her","their","we",
    "you","i","me","my","our","your","who","whom","what","which","whose","about","also","says","said",
    "say","according","claim","claims","report","reports","reported","hai","hain","ki","ka","ke","ko","se"
}

REFUTE_CUES = {
    "false", "fake", "hoax", "debunked", "misleading", "incorrect", "untrue",
    "no evidence", "not true", "fabricated", "rumor", "rumour", "scam", "fraud",
    "manipulated", "out of context", "disputed", "denied", "incorrectly", "jhoot", "galat"
}

BUILTIN_KB = [
    {"title": "Earth orbits the Sun", "source": "Science Reference",
     "snippet": "The Earth revolves around the Sun in an elliptical orbit, completing one revolution in about 365.25 days."},
    {"title": "Water boils at 100 C at sea level", "source": "Physics Reference",
     "snippet": "At standard atmospheric pressure (sea level), pure water boils at 100 degrees Celsius."},
    {"title": "Moon landing was real", "source": "Space History",
     "snippet": "Apollo 11 landed humans on the Moon on 20 July 1969; the landing is confirmed by independent tracking and retroreflectors left on the surface."},
    {"title": "Vaccines are safe and effective", "source": "WHO",
     "snippet": "Vaccines are rigorously tested and monitored; they are one of the most effective tools for preventing serious disease."},
    {"title": "Global temperatures are rising", "source": "Climate Data",
     "snippet": "Instrumental records show global average surface temperature has risen about 1.1 C since the late 1800s."},
    {"title": "Humans need water to survive", "source": "Biology Reference",
     "snippet": "Water is essential for human life; survival without water is typically limited to a few days."},
    {"title": "The Great Wall of China is visible from the Moon — DEBUNKED", "source": "Fact Check",
     "snippet": "This is false. The Great Wall is not visible from the Moon with the naked eye; the claim is a myth."},
    {"title": "Cracking knuckles does not cause arthritis", "source": "Medical Study",
     "snippet": "Studies find no link between knuckle cracking and arthritis, though it may annoy people nearby."},
    {"title": "Humans use only 10 percent of their brains — FALSE", "source": "Neuroscience Fact Check",
     "snippet": "This claim is untrue. Brain imaging shows activity across virtually all brain regions throughout the day."},
]


def extract_keywords(text: str, top_k: int = 8) -> list[str]:
    tokens = re.findall(r"[\w]+", text.lower())
    freq = {}
    for t in tokens:
        if t not in STOPWORDS and len(t) > 2:
            freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:top_k]]


def similarity(query_keywords: list[str], text: str) -> float:
    text_tokens = set(re.findall(r"[\w]+", text.lower()))
    if not query_keywords:
        return 0.0
    hits = sum(1 for k in query_keywords if k in text_tokens)
    return hits / len(query_keywords)


def classify_stance(text: str, similarity_score: float) -> str:
    text_lower = text.lower()
    if any(cue in text_lower for cue in REFUTE_CUES):
        return "DISAGREES"
    elif similarity_score >= 0.4:
        return "AGREES"
    return "NEUTRAL"


class NewsAPIProvider:
    name = "NewsAPI"

    def search(self, keywords: list[str], limit: int = MAX_EVIDENCE) -> list[dict]:
        q = urllib.parse.quote(" ".join(keywords))
        url = f"https://newsapi.org/v2/everything?q={q}&pageSize={limit}&sortBy=relevancy&apiKey={NEWSAPI_KEY}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            return [
                {"title": a.get("title", ""), "source": a.get("source", {}).get("name", "News"),
                 "snippet": a.get("description") or a.get("content", ""),
                 "url": a.get("url")}
                for a in data.get("articles", [])
            ]
        except Exception:
            return []


class BuiltinEvidenceProvider:
    name = "Builtin Knowledge Pool"

    def search(self, keywords: list[str], limit: int = MAX_EVIDENCE) -> list[dict]:
        return BUILTIN_KB[:]


def get_provider():
    if NEWSAPI_KEY:
        return NewsAPIProvider()
    return BuiltinEvidenceProvider()


def verify_claim(claim: str) -> dict:
    keywords = extract_keywords(claim)
    provider = get_provider()
    candidates = provider.search(keywords)

    scored = []
    for ev in candidates:
        sim = similarity(keywords, ev["title"] + " " + ev["snippet"])
        if sim > 0:
            scored.append((sim, ev))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:MAX_EVIDENCE]

    evidence = [
        {
            "source": ev["source"],
            "title": ev["title"],
            "snippet": ev["snippet"],
            "url": ev.get("url"),
            "similarity": round(sim, 3),
            "stance": classify_stance(ev["title"] + " " + ev["snippet"], sim)
        }
        for sim, ev in top
    ]

    if not top:
        return {"verdict": "NOT ENOUGH INFO", "confidence": 0.2, "keywords": keywords,
                "provider": provider.name, "evidence": [],
                "signals": ["No relevant evidence could be retrieved for the extracted keywords."]}

    best_sim = top[0][0]
    combined_text = " ".join(ev["snippet"].lower() for _, ev in top[:3])
    refute_hit = any(cue in combined_text for cue in REFUTE_CUES)

    if refute_hit and best_sim >= 0.3:
        verdict, confidence = "REFUTED", min(0.95, best_sim + REFUTE_CUE_BONUS)
    elif best_sim >= SUPPORT_THRESHOLD:
        verdict, confidence = "SUPPORTED", min(0.95, best_sim + 0.1)
    elif best_sim >= 0.25:
        verdict, confidence = "NOT ENOUGH INFO", round(best_sim + 0.1, 2)
    else:
        verdict, confidence = "NOT ENOUGH INFO", round(best_sim, 2)

    signals = [
        f"Keywords extracted: {', '.join(keywords)}",
        f"Evidence provider: {provider.name}",
        f"Best evidence match: {round(best_sim * 100)}% keyword overlap",
    ]
    if refute_hit:
        signals.append("Contradiction/debunking cues detected in retrieved evidence.")
    if verdict == "NOT ENOUGH INFO":
        signals.append("Evidence is weak or ambiguous — treat the claim as unverified.")

    return {"verdict": verdict, "confidence": round(confidence, 2), "keywords": keywords,
            "provider": provider.name, "evidence": evidence, "signals": signals}
