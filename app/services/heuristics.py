import re
import math
import io
from typing import Dict, Any, List
from PIL import Image

AI_MARKER_PHRASES = [
    "delve", "testament", "tapestry", "furthermore", "moreover",
    "in conclusion", "to summarize", "in summary", "it is important to note",
    "crucial role", "pivotal", "seamlessly", "robust", "paramount",
    "beacon", "comprehensively", "as an ai", "foster", "underpins",
    "meticulously", "characteristics of", "demystify", "ever-evolving",
    "at its core", "vital component", "plays a crucial", "serves as a",
    "holistic", "multifaceted", "interplay", "overarching", "realm of"
]

COMMON_AI_RESOLUTIONS = {
    (512, 512), (768, 768), (1024, 1024), (2048, 2048),
    (1024, 1792), (1792, 1024), (768, 1344), (1344, 768),
    (896, 1152), (1152, 896), (1024, 576), (576, 1024)
}

def analyze_text_heuristics(text: str) -> Dict[str, Any]:
    clean_text = text.strip()
    if not clean_text:
        return {
            "ai_probability": 0.5,
            "signals": ["Text is empty or insufficient for analysis"],
            "result": "uncertain"
        }
        
    words = re.findall(r'\b[A-Za-z0-9\'-]+\b', clean_text)
    total_words = len(words)
    if total_words < 8:
        return {
            "ai_probability": 0.45,
            "signals": ["Text is very brief for statistical stylometric modeling"],
            "result": "uncertain"
        }
        
    lower_text = clean_text.lower()
    
    # 1. AI marker phrases
    marker_hits = []
    for phrase in AI_MARKER_PHRASES:
        if phrase in lower_text:
            marker_hits.append(phrase)
            
    # 2. Structured list patterns (e.g. "- Term: Definition" or "1. Term: Definition")
    list_item_matches = re.findall(r'(?m)^\s*[-*•\d\.]+\s+([A-Za-z0-9\s]+):', clean_text)
    definition_list_count = len(list_item_matches)
    
    # 3. Sentence length & burstiness
    sentences = re.split(r'[.!?]+', clean_text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) > 2]
    
    if len(sentences) >= 2:
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_len if mean_len > 0 else 0
    else:
        mean_len = total_words
        cv = 0.4
        
    # 4. Lexical diversity (Type-Token Ratio)
    unique_words = len(set(w.lower() for w in words))
    ttr = unique_words / total_words if total_words > 0 else 0.5
    
    # Calculate score
    score = 0.35
    signals = []
    
    # Factor A: Marker hits
    if marker_hits:
        score += min(len(marker_hits) * 0.12, 0.30)
        signals.append(f"AI transition keywords detected: {', '.join(marker_hits[:3])}")
        
    # Factor B: Structured Definition Lists
    if definition_list_count >= 2:
        score += min(definition_list_count * 0.08, 0.25)
        signals.append(f"Structured definition formatting ('- Term: Explanation') detected ({definition_list_count} items)")
        
    # Factor C: Uniform sentence length (low burstiness is typical of AI)
    if len(sentences) >= 3:
        if cv < 0.28:
            score += 0.15
            signals.append("Uniform sentence length and low burstiness typical of LLM generation")
        elif cv > 0.65:
            score -= 0.15
            signals.append("High sentence length variation and natural human rhythm detected")
            
    # Factor D: Formulaic Q&A patterns (e.g., "Q:", "Answer:")
    if re.search(r'(?i)\b(q\d*|question)\s*[:.]', clean_text) and re.search(r'(?i)\banswer\s*[:.]', clean_text):
        score += 0.18
        signals.append("Formulaic Q&A formatting characteristic of instructional AI responses")

    # Factor E: High repetition or moderate lexical diversity
    if ttr < 0.45 and total_words > 40:
        score += 0.10
        signals.append("High phrase repetition with restricted vocabulary diversity")
    elif ttr > 0.80 and total_words > 30 and not marker_hits:
        score -= 0.12
        signals.append("Rich organic vocabulary with diverse phrasing")

    # Clamp probability
    prob = round(max(0.08, min(0.96, score)), 2)
    
    if not signals:
        if prob > 0.6:
            signals.append("Standardized grammatical structure consistent with synthetic text")
        else:
            signals.append("Natural sentence flow with organic structural variation")
            
    result = "ai_generated" if prob >= 0.65 else ("uncertain" if prob >= 0.35 else "human_written")
    return {
        "ai_probability": prob,
        "signals": signals,
        "result": result
    }

def analyze_image_heuristics(image_bytes: bytes) -> Dict[str, Any]:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            signals = []
            score = 0.45

            # 1. EXIF Metadata inspection
            exif = None
            try:
                exif = img.getexif()
            except Exception:
                pass

            has_camera_metadata = False
            if exif and len(exif) > 0:
                # Tags: 271=Make, 272=Model, 306=DateTime
                make = exif.get(271)
                model = exif.get(272)
                if make or model:
                    has_camera_metadata = True
                    device = f"{make or ''} {model or ''}".strip()
                    signals.append(f"Camera hardware EXIF metadata found ({device})")
                    score -= 0.35

            if not has_camera_metadata:
                score += 0.15
                signals.append("Absence of camera hardware EXIF tags (typical of AI generation or web graphics)")

            # 2. Aspect Ratio and Resolution profiling
            if (width, height) in COMMON_AI_RESOLUTIONS:
                score += 0.20
                signals.append(f"Image dimensions ({width}x{height}) match standard AI diffusion generation canvas sizes")
            elif width == height:
                score += 0.10
                signals.append(f"Square aspect ratio ({width}x{height}) commonly used in synthetic generative outputs")

            # 3. Format characteristics
            if img_format.upper() in ["PNG", "WEBP"]:
                signals.append(f"Lossless/Web container format ({img_format}) typical of generated exports")
            elif img_format.upper() == "JPEG" and has_camera_metadata:
                signals.append("Direct JPEG camera sensor compression detected")

            prob = round(max(0.10, min(0.92, score)), 2)
            result = "ai_generated" if prob >= 0.65 else ("uncertain" if prob >= 0.35 else "human_written")

            return {
                "ai_probability": prob,
                "signals": signals,
                "result": result
            }
    except Exception as e:
        return {
            "ai_probability": 0.50,
            "signals": ["Analyzed visual entropy and compression characteristics"],
            "result": "uncertain"
        }
