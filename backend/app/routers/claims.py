import json
import re
from fastapi import APIRouter, Depends
from ..schemas import ClaimRequest, UrlVerificationRequest, BatchClaimRequest, BatchAnalysisResponse, AnalysisResponse
from ..deps import get_current_user
from ..services import claim_service, url_service
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


@router.post("/verify-url", response_model=AnalysisResponse)
def verify_url(body: UrlVerificationRequest, user=Depends(get_current_user)):
    result = url_service.verify_url_article(body.url)
    claim_text = result.get("extracted_claim", body.url)
    
    analysis_id = models.create_analysis(
        user_id=user["id"],
        analysis_type="claim",
        input_text=f"URL Article: {body.url} -> Claim: {claim_text}",
        verdict=result["verdict"],
        confidence=result["confidence"],
        signals=json.dumps(result["signals"]),
        evidence=json.dumps(result.get("evidence", [])),
    )
    return AnalysisResponse(
        id=analysis_id,
        analysis_type="claim",
        verdict=result["verdict"],
        confidence=result["confidence"],
        signals=result["signals"],
        evidence=result.get("evidence", [])
    )


@router.post("/verify-batch", response_model=BatchAnalysisResponse)
def verify_batch(body: BatchClaimRequest, user=Depends(get_current_user)):
    results = []
    for claim in body.claims:
        res = claim_service.verify_claim(claim)
        analysis_id = models.create_analysis(
            user_id=user["id"],
            analysis_type="claim",
            input_text=claim,
            verdict=res["verdict"],
            confidence=res["confidence"],
            signals=json.dumps(res["signals"]),
            evidence=json.dumps(res["evidence"]),
        )
        results.append(AnalysisResponse(
            id=analysis_id,
            analysis_type="claim",
            verdict=res["verdict"],
            confidence=res["confidence"],
            signals=res["signals"],
            evidence=res["evidence"]
        ))
    return BatchAnalysisResponse(total_processed=len(results), results=results)
