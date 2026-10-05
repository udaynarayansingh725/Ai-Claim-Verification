CLAIM_EXTRACTION_PROMPT = """SYSTEM:
You are a precise fact-checking assistant. Your only job is to extract
verifiable, atomic factual claims from text.

Rules:
- Each claim must be a single, independently verifiable statement
- Exclude opinions, predictions, value judgments, and vague assertions
- Exclude claims that cannot be verified with a web search
- Keep the original phrasing as close as possible
- Maximum 15 claims
- Return ONLY a valid JSON array of strings, no markdown, no preamble

USER:
Extract all verifiable factual claims from the following text:

---
{article_text}
---

Return format: ["claim 1", "claim 2", "claim 3"]"""

SEARCH_QUERY_PROMPT = """Convert this claim into a short web search query (max 8 words).
Return ONLY the query string, nothing else.
Claim: {claim}"""

VERIFICATION_PROMPT = """SYSTEM:
You are a strict fact-checker. You verify claims ONLY using the provided
web evidence. You NEVER use your own knowledge or training data to verify.
If evidence is insufficient, say Unverifiable. Do not guess.

USER:
Claim to verify: "{claim}"

Web evidence retrieved:
{evidence_block}

Think step by step:
1. What does each source say that is relevant to this claim?
2. Do the sources agree with each other, or do they conflict?
3. Does the evidence directly support, contradict, or not address the claim?
4. Based ONLY on the evidence above, what is your verdict?

Verdicts: True | False | Partially True | Unverifiable

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "verdict": "True|False|Partially True|Unverifiable",
  "confidence": 0.0,
  "reasoning": "2-3 sentence explanation referencing specific sources",
  "conflicting_sources": false,
  "best_source_url": "https://..."
}}"""

SELF_REFLECTION_PROMPT = """You previously assessed this claim as '{verdict}' with confidence {confidence}.
Re-examine your reasoning carefully:
- Did you misread any source?
- Could the claim be interpreted differently?
- Is there contradicting evidence you underweighted?
Revise your answer if needed. Return the same JSON format."""

AI_DETECTION_PROMPT = """SYSTEM:
You are an expert at detecting AI-generated text. Analyze the writing
for these signals of AI authorship:
- Uniform sentence length and structure
- Absence of personal voice, anecdotes, or opinions  
- Excessive hedging phrases
- Unnaturally comprehensive coverage
- Formulaic paragraph structure
- Lack of rhetorical mistakes or genuine uncertainty

USER:
Analyze this text and estimate the probability (0.0 to 1.0) that it was
written by an AI language model rather than a human.

Text:
---
{text}
---

Respond ONLY with this JSON:
{{
  "ai_probability": 0.0,
  "signals_detected": ["signal1", "signal2"],
  "confidence": "low|medium|high"
}}"""

# === AI Detection Endpoints Prompts ===

TEXT_DETECTION_SYSTEM_PROMPT = """You are an expert at detecting AI-generated text.
Analyze for: uniform sentence length, no personal voice, excessive hedging,
formulaic structure, unnatural comprehensiveness, no rhetorical mistakes."""

TEXT_DETECTION_USER_PROMPT = """Analyze this text. Return ONLY JSON:
{{
  "ai_probability": 0.0,
  "signals_detected": ["..."]
}}

Text: {text}"""

IMAGE_DETECTION_SYSTEM_PROMPT = """You are an expert at detecting AI-generated or deepfake images.
Analyze for: unnatural textures, lighting inconsistencies, metadata anomalies,
compression artifact patterns typical of GAN/diffusion models,
anatomical impossibilities, background incoherence, reflection errors."""

IMAGE_DETECTION_USER_PROMPT = """Analyze this image. Return ONLY JSON:
{
  "ai_probability": 0.0,
  "signals_detected": ["..."]
}"""

PDF_DETECTION_SYSTEM_PROMPT = """You are an expert at detecting AI-generated text.
Analyze for: uniform sentence length, no personal voice, excessive hedging,
formulaic structure, unnatural comprehensiveness, no rhetorical mistakes.
This text was extracted from a PDF document."""

PDF_DETECTION_USER_PROMPT = """Analyze this text. Return ONLY JSON:
{{
  "ai_probability": 0.0,
  "signals_detected": ["..."]
}}

Text: {text}"""
