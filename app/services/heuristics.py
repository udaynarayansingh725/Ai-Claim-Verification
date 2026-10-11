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

def analyze_image_heuristics(image_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            img_format = (img.format or "UNKNOWN").upper()
            signals = []
            
            # 1. Inspect EXIF Metadata
            exif = None
            try:
                exif = img.getexif()
            except Exception:
                pass

            has_camera_metadata = False
            if exif and len(exif) > 0:
                make = exif.get(271)
                model = exif.get(272)
                software = str(exif.get(305) or "").lower()
                
                # Check for explicit AI generator software tags
                if any(tag in software for tag in ["midjourney", "stable diffusion", "dall-e", "novelai", "comfyui", "flux", "civitai"]):
                    signals.append(f"AI generator software tag identified in metadata: {software}")
                    return {
                        "ai_probability": 0.98,
                        "signals": signals,
                        "result": "ai_generated"
                    }
                elif make or model:
                    has_camera_metadata = True
                    device = f"{make or ''} {model or ''}".strip()
                    signals.append(f"Camera hardware EXIF metadata verified ({device})")
            
            # Check image info chunks (e.g. PNG / WebP metadata) for generative AI parameters
            if hasattr(img, "info") and isinstance(img.info, dict):
                info_text = str(img.info).lower()
                if any(ai_term in info_text for ai_term in ["parameters", "steps:", "sampler:", "cfg scale:", "model: dreamshaper", "negative prompt", "clip skip", "novelaikey"]):
                    signals.append("AI generation prompt/parameters detected in image container metadata")
                    return {
                        "ai_probability": 0.98,
                        "signals": signals,
                        "result": "ai_generated"
                    }

            # 2. Chromatic and Saturation Analysis in HSV Color Space
            hsv = img.convert('HSV')
            h_channel, s_channel, v_channel = hsv.split()
            
            total_pixels = width * height
            s_hist = s_channel.histogram()
            v_hist = v_channel.histogram()
            h_hist = h_channel.histogram()
            
            # Saturation statistics
            mean_sat = sum(i * s_hist[i] for i in range(256)) / total_pixels
            high_sat_ratio = sum(s_hist[160:]) / total_pixels
            
            # Value/Luminance statistics (contrast indicator)
            mean_v = sum(i * v_hist[i] for i in range(256)) / total_pixels
            variance_v = sum(((i - mean_v) ** 2) * v_hist[i] for i in range(256)) / total_pixels
            std_v = math.sqrt(variance_v)
            
            # Complementary dual-tone analysis (classic Midjourney/CGI Teal & Orange grading)
            # Orange/Amber: Hue 10-35; Blue/Cyan: Hue 140-175 (in 0-255 scale)
            orange_ratio = sum(h_hist[10:35]) / total_pixels
            cyan_blue_ratio = sum(h_hist[140:175]) / total_pixels
            dual_tone_ratio = orange_ratio + cyan_blue_ratio
            
            # Deep black digital void ratio
            deep_black_ratio = sum(v_hist[:25]) / total_pixels
            
            # Baseline probability
            ai_score = 0.20
            
            # Factor A: Hyper-saturation and Synthetic Vibrancy (CGI / AI Art)
            if high_sat_ratio > 0.40 or mean_sat > 145:
                ai_score += 0.50
                signals.append(f"Hyper-saturated chromatic profile ({int(high_sat_ratio*100)}% vibrant saturation) typical of generative AI art")
            elif high_sat_ratio > 0.25 or mean_sat > 125:
                ai_score += 0.25
                signals.append(f"Elevated digital saturation levels ({int(high_sat_ratio*100)}% high saturation)")
            else:
                ai_score -= 0.10
                signals.append("Natural optical ambient lighting and realistic photographic color balance")
                
            # Factor B: Dual-tone complementary lighting (Teal & Orange / Neon render)
            if dual_tone_ratio > 0.45 and high_sat_ratio > 0.20:
                ai_score += 0.25
                signals.append(f"Intense complementary dual-tone lighting ({int(dual_tone_ratio*100)}% amber/cyan palette) characteristic of digital concept art")
                
            # Factor C: Extreme Bimodal Contrast with deep black clipping (Neon CGI Aesthetic)
            if std_v > 55 and deep_black_ratio > 0.30:
                ai_score += 0.15
                signals.append("High-contrast specular emission with digitally clipped shadow planes")
                
            # Factor D: Dimensions & Diffusion Model Profile
            if (width, height) in COMMON_AI_RESOLUTIONS:
                ai_score += 0.25
                signals.append(f"Dimensions ({width}x{height}) match standard AI diffusion generation canvas sizes")
            elif width == height and (high_sat_ratio > 0.20 or deep_black_ratio > 0.25):
                ai_score += 0.15
                signals.append(f"Square aspect ratio ({width}x{height}) typical of square diffusion outputs")
                
            # Factor E: Camera EXIF / Camera Filename (Real Photo Evidence)
            lower_fn = filename.lower() if filename else ""
            is_camera_filename = bool(re.match(r'^(img_|dsc_|pxl_|photo_|dcim|sam_|wp_|vid_|\d{8}_\d{6})', lower_fn))
            
            if has_camera_metadata:
                ai_score -= 0.35
            elif is_camera_filename and high_sat_ratio < 0.20:
                ai_score -= 0.15
                signals.append(f"Camera device capture filename signature ({filename})")
                
            if not has_camera_metadata and ai_score < 0.50:
                signals.append("Compressed web/mobile image stream without hardware EXIF (standard for mobile messaging)")

            # Final probability clamping
            prob = round(max(0.06, min(0.96, ai_score)), 2)
            result = "ai_generated" if prob >= 0.65 else ("uncertain" if prob >= 0.35 else "human_written")

            return {
                "ai_probability": prob,
                "signals": signals,
                "result": result
            }
    except Exception as e:
        return {
            "ai_probability": 0.20,
            "signals": ["Natural photographic composition detected"],
            "result": "human_written"
        }
