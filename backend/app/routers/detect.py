import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..schemas import TextDetectRequest, AnalysisResponse
from ..deps import get_current_user
from ..services import text_ai_service, image_ai_service
from .. import models

router = APIRouter(prefix="/api", tags=["detect"])

MAX_IMAGE_MB = 10
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


@router.post("/detect-text", response_model=AnalysisResponse)
def detect_text(body: TextDetectRequest, user=Depends(get_current_user)):
    result = text_ai_service.analyze(body.text)
    analysis_id = models.create_analysis(
        user_id=user["id"], analysis_type="text", input_text=body.text,
        verdict=result["verdict"], confidence=result["confidence"],
        signals=json.dumps(result["signals"]),
    )
    return AnalysisResponse(id=analysis_id, analysis_type="text",
                            verdict=result["verdict"], confidence=result["confidence"],
                            signals=result["signals"])


@router.post("/detect-image", response_model=AnalysisResponse)
def detect_image(file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, WEBP or BMP images are allowed")
    data = file.file.read()
    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(400, f"Image too large (max {MAX_IMAGE_MB} MB)")

    result = image_ai_service.analyze_image(data, filename=file.filename)
    analysis_id = models.create_analysis(
        user_id=user["id"], analysis_type="image", input_image=file.filename,
        verdict=result["verdict"], confidence=result["confidence"],
        signals=json.dumps(result["signals"]),
    )
    return AnalysisResponse(id=analysis_id, analysis_type="image",
                            verdict=result["verdict"], confidence=result["confidence"],
                            signals=result["signals"])
