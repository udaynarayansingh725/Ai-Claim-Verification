"""AI-generated image detection & Error Level Analysis (ELA) Heatmap generation.

Analyses interpretable signals using Pillow + numpy:
  - EXIF/metadata presence
  - Error Level Analysis (ELA) map & visual heatmap generator
  - High-frequency FFT spectrum ratio
  - Saturation distribution & variance
"""
import io
import base64
import numpy as np
from PIL import Image, ImageEnhance


def _to_rgb(img: Image.Image) -> Image.Image:
    return img.convert("RGB")


def _generate_ela_heatmap(img: Image.Image, max_dim: int = 400) -> tuple[float, str]:
    """Generates ELA std score and base64-encoded visual ELA heatmap."""
    # Resize thumbnail copy for fast performance
    img_copy = img.copy()
    img_copy.thumbnail((max_dim, max_dim))
    rgb = _to_rgb(img_copy)
    
    buf = io.BytesIO()
    rgb.save(buf, "JPEG", quality=90)
    buf.seek(0)
    resaved = Image.open(buf).convert("RGB")
    
    arr_orig = np.asarray(rgb).astype(np.int16)
    arr_resaved = np.asarray(resaved).astype(np.int16)
    diff = np.abs(arr_orig - arr_resaved).astype(np.uint8)
    
    # Calculate ELA block variance std
    ela_gray = diff.mean(axis=2)
    h, w = ela_gray.shape
    bh, bw = max(h // 16, 1), max(w // 16, 1)
    blocks = [ela_gray[y:y + bh, x:x + bw] for y in range(0, h - bh + 1, bh)
              for x in range(0, w - bw + 1, bw)]
    std_score = float(np.array([b.mean() for b in blocks]).std()) if blocks else 0.0

    # Scale diff for visual heatmap display
    visual_diff = Image.fromarray(np.clip(diff * 12, 0, 255).astype(np.uint8))
    enhanced = ImageEnhance.Brightness(visual_diff).enhance(1.8)
    
    out_buf = io.BytesIO()
    enhanced.save(out_buf, format="PNG")
    b64_map = "data:image/png;base64," + base64.b64encode(out_buf.getvalue()).decode("utf-8")
    
    return std_score, b64_map


def _fft_score(gray: np.ndarray) -> float:
    """Ratio of high-frequency radial energy."""
    f = np.fft.fftshift(np.fft.fft2(gray))
    mag = np.abs(f)
    h, w = mag.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    r_max = r.max()
    low = mag[r < 0.25 * r_max].sum()
    high = mag[r > 0.6 * r_max].sum()
    if low <= 0:
        return 0.0
    return float(high / (low + high))


def analyze_image(data: bytes, filename: str = "") -> dict:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        return {"verdict": "Invalid image", "confidence": 0.0,
                "signals": ["File could not be decoded as an image."], "features": {}}

    rgb = _to_rgb(img)
    arr = np.asarray(rgb).astype(np.float32)
    gray = np.asarray(rgb.convert("L")).astype(np.float32)

    # 1. Metadata
    try:
        exif = img.getexif() if hasattr(img, "getexif") else (img._getexif() if hasattr(img, "_getexif") else None)
        has_metadata = bool(exif and len(exif) > 0)
        metadata_score = 0.0 if has_metadata else 0.6
    except Exception:
        has_metadata = False
        metadata_score = 0.6

    # 2. ELA uniformity & Heatmap
    ela_std, ela_heatmap_b64 = _generate_ela_heatmap(rgb)
    ela_score = 1.0 - min(ela_std / 3.0, 1.0)

    # 3. FFT high-frequency ratio
    fft_ratio = _fft_score(gray)
    fft_score = 1.0 - min(fft_ratio / 0.15, 1.0)

    # 4. Saturation statistics
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat = np.zeros_like(mx)
    mask = mx > 0
    sat[mask] = (mx[mask] - mn[mask]) / mx[mask]
    sat_mean, sat_std = float(sat.mean()), float(sat.std())
    sat_score = 1.0 - min(sat_std / 0.25, 1.0)

    likelihood = (0.15 * metadata_score + 0.35 * ela_score +
                  0.30 * fft_score + 0.20 * sat_score)
    likelihood = round(min(max(likelihood, 0.02), 0.98), 2)

    verdict = ("Likely AI-generated" if likelihood >= 0.65 else
               "Possibly AI-generated" if likelihood >= 0.40 else
               "Likely a real photograph")

    signals = [
        f"EXIF/metadata: {'present (real-camera indicator)' if has_metadata else 'missing (common in AI images)'}",
        f"ELA uniformity: std={ela_std:.2f} — {'very uniform (AI-like)' if ela_score > 0.6 else 'normal variation'}",
        f"High-frequency spectrum ratio: {fft_ratio:.3f} — {'low (AI-like)' if fft_score > 0.6 else 'typical of camera photos'}",
        f"Saturation stats: mean={sat_mean:.2f}, std={sat_std:.2f}",
        "NOTE: JPEG re-compression, filters and screenshots can affect these signals.",
        "This is a probabilistic signal, not proof of origin.",
    ]

    return {
        "verdict": verdict,
        "confidence": likelihood,
        "signals": signals,
        "ela_heatmap": ela_heatmap_b64,
        "features": {
            "metadata_score": round(metadata_score, 3),
            "ela_score": round(ela_score, 3),
            "fft_score": round(fft_score, 3),
            "saturation_score": round(sat_score, 3),
            "format": img.format,
            "size": list(img.size)
        }
    }
