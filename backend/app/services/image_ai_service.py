"""AI-generated image detection.

Analyses interpretable signals using Pillow + numpy:
  - EXIF/metadata presence (AI generators usually strip metadata)
  - Error Level Analysis (ELA) uniformity (re-encode at quality 90 and measure
    per-block differences — AI images tend to be unusually uniform)
  - High-frequency energy in FFT (GAN/diffusion spectra differ from camera noise)
  - Saturation statistics

IMPORTANT (responsible use): the score is a probabilistic signal, NOT proof.
"""
import io
import numpy as np
from PIL import Image, ImageFilter, ExifTags


def _to_rgb(img: Image.Image) -> Image.Image:
    return img.convert("RGB")


def _ela_score(img: Image.Image) -> float:
    """Mean block-level variance of ELA map. Low variance => uniform => AI-like."""
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    buf.seek(0)
    resaved = Image.open(buf).convert("RGB")
    ela = np.abs(np.asarray(img).astype(np.int16) - np.asarray(resaved).astype(np.int16)).mean(axis=2)

    h, w = ela.shape
    bh, bw = max(h // 16, 1), max(w // 16, 1)
    blocks = [ela[y:y + bh, x:x + bw] for y in range(0, h - bh + 1, bh)
              for x in range(0, w - bw + 1, bw)]
    if not blocks:
        return 0.0
    block_means = np.array([b.mean() for b in blocks])
    return float(block_means.std())


def _fft_score(gray: np.ndarray) -> float:
    """Ratio of high-frequency radial energy. Camera photos usually have more."""
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
        metadata_score = 0.0 if has_metadata else 0.6   # no metadata -> slightly AI-like
    except Exception:
        has_metadata = False
        metadata_score = 0.6

    # 2. ELA uniformity
    ela_std = _ela_score(rgb)
    ela_score = 1.0 - min(ela_std / 3.0, 1.0)           # uniform ELA -> AI-like

    # 3. FFT high-frequency ratio
    fft_ratio = _fft_score(gray)
    fft_score = 1.0 - min(fft_ratio / 0.15, 1.0)        # low HF energy -> AI-like

    # 4. Saturation statistics
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat = np.zeros_like(mx)
    mask = mx > 0
    sat[mask] = (mx[mask] - mn[mask]) / mx[mask]
    sat_mean, sat_std = float(sat.mean()), float(sat.std())
    sat_score = 1.0 - min(sat_std / 0.25, 1.0)          # flat saturation -> AI-like

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

    return {"verdict": verdict, "confidence": likelihood, "signals": signals,
            "features": {"metadata_score": round(metadata_score, 3),
                         "ela_score": round(ela_score, 3),
                         "fft_score": round(fft_score, 3),
                         "saturation_score": round(sat_score, 3),
                         "format": img.format, "size": list(img.size)}}
