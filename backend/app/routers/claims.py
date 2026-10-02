import json
from fastapi import APIRouter, Depends
from ..schemas import ClaimRequest, AnalysisResponse
from ..deps import get_current_user
from ..services import claim_service
from .. import models

router = APIRouter(prefix="/api", tags=["claims"])


@router.post("/verify-claim", response_model=AnalysisResponse)
def verify_claim(body: ClaimRequest, user=Depends(get_current_user)):
    result = claim_service.verify_claim(body.claim)

    analysis_id = models.create_analysis(
        user_id=user["id"],
        analysis_type="claim",
        input_text=body.claim,
        verdict=result["verdict"],
        confidence=result["confidence"],
        signals=json.dumps(result["signals"]),
        evidence=json.dumps(result["evidence"]),
    )
    return AnalysisResponse(id=analysis_id, analysis_type="claim",
                            verdict=result["verdict"], confidence=result["confidence"],
                            signals=result["signals"], evidence=result["evidence"])
