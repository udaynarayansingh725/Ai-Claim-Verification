"""AI-generated text detection.

Produces a *probabilistic likelihood* score from interpretable signals:
  - burstiness (sentence-length variance — human writing varies more)
  - lexical diversity (type-token ratio)
  - repetition (repeated n-grams)
  - AI-typical connective phrases
  - punctuation/formality patterns

IMPORTANT (responsible use): the score is a signal, NOT proof of authorship.
"""
import re
import math

AI_PHRASES = [
    "as an ai language model", "it is important to note", "in today's digital age",
    "delve into", "furthermore", "moreover", "in conclusion", "overall",
    "it's worth noting", "in summary", "additionally", "in today's fast-paced world",
    "navigate the landscape", "landscape of", "underscores", "highlighting the importance",
    "plays a crucial role", "plays a vital role", "a testament to", "when it comes to",
    "the world of", "in the realm of", "serves as a reminder", "it goes without saying",
]


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if len(s.strip()) > 1]


def _ngrams(tokens, n):
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def analyze(text: str) -> dict:
    text_lower = text.lower()
    sents = _sentences(text)
    tokens = re.findall(r"[a-z']+", text_lower)
    n = max(len(tokens), 1)

    # 1. Burstiness: human writing has higher sentence-length variance
    if len(sents) >= 3:
        lengths = [len(s.split()) for s in sents]
        mean = sum(lengths) / len(lengths)
        var = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        cv = math.sqrt(var) / max(mean, 1)                     # coefficient of variation
        burstiness_score = 1.0 - min(cv / 0.8, 1.0)            # low CV -> AI-like
    else:
        burstiness_score = 0.5

    # 2. Lexical diversity
    ttr = len(set(tokens)) / n
    lexical_score = 1.0 - min(ttr / 0.65, 1.0)                 # low diversity -> AI-like

    # 3. Repetition of 4-grams
    grams = _ngrams(tokens, 4)
    if grams:
        unique_ratio = len(set(grams)) / len(grams)
        repetition_score = 1.0 - unique_ratio
    else:
        repetition_score = 0.0

    # 4. AI-typical phrases
    phrase_hits = [p for p in AI_PHRASES if p in text_lower]
    phrase_score = min(len(phrase_hits) / 3.0, 1.0)

    # 5. Formal connective density (transition words per sentence)
    connectors = ("however", "therefore", "thus", "consequently", "in addition",
                  "on the other hand", "for instance", "for example", "in contrast")
    conn_count = sum(text_lower.count(c) for c in connectors)
    connector_score = min(conn_count / max(len(sents), 1) / 0.5, 1.0)

    # Weighted ensemble (weights sum to 1)
    likelihood = (0.30 * burstiness_score + 0.20 * lexical_score +
                  0.15 * repetition_score + 0.25 * phrase_score +
                  0.10 * connector_score)
    likelihood = round(min(max(likelihood, 0.02), 0.98), 2)

    verdict = ("Likely AI-generated" if likelihood >= 0.65 else
               "Possibly AI-generated" if likelihood >= 0.40 else
               "Likely human-written")

    signals = [
        f"Burstiness (sentence-length variation): {'low (AI-like)' if burstiness_score > 0.6 else 'moderate/high (human-like)'} — score {burstiness_score:.2f}",
        f"Lexical diversity (type-token ratio {ttr:.2f}): {'low (AI-like)' if lexical_score > 0.6 else 'normal (human-like)'}",
        f"Repeated 4-gram ratio: {repetition_score:.2f} ({'elevated' if repetition_score > 0.15 else 'normal'})",
    ]
    if phrase_hits:
        signals.append(f"AI-typical phrases detected: {', '.join(phrase_hits[:3])}")
    if connector_score > 0.6:
        signals.append("Dense use of formal connectives/transition phrases (common in AI text).")
    signals.append("NOTE: This is a probabilistic signal, not proof of authorship.")

    return {"verdict": verdict, "confidence": likelihood, "signals": signals,
            "features": {"burstiness": round(burstiness_score, 3),
                         "lexical_diversity": round(lexical_score, 3),
                         "repetition": round(repetition_score, 3),
                         "ai_phrases": round(phrase_score, 3),
                         "connectors": round(connector_score, 3)}}
