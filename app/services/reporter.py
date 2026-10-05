from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Report, Claim
from app.schemas.api import ClaimResult
import uuid

def calculate_score(claims: list[ClaimResult]) -> float:
    weights = {"True": 1.0, "Partially True": 0.5, "False": 0.0}
    
    weighted_sum = 0.0
    confidence_sum = 0.0
    
    for c in claims:
        if c.verdict in weights and c.confidence is not None:
            weight = weights[c.verdict]
            weighted_sum += weight * c.confidence
            confidence_sum += c.confidence
            
    if confidence_sum == 0.0:
        return 0.0
        
    return round(weighted_sum / confidence_sum, 3)

async def save_report(
    db: AsyncSession, 
    input_text: str, 
    source_url: str | None, 
    ai_prob: float, 
    claims_results: list[ClaimResult]
) -> str:
    overall_score = calculate_score(claims_results)
    report_id = uuid.uuid4()
    
    report = Report(
        id=report_id,
        input_text=input_text,
        source_url=source_url,
        overall_score=overall_score,
        ai_text_probability=ai_prob
    )
    db.add(report)
    
    for c in claims_results:
        claim_record = Claim(
            id=uuid.uuid4(),
            report_id=report_id,
            claim_text=c.text,
            verdict=c.verdict,
            confidence=c.confidence,
            reasoning=c.reasoning,
            sources=[s.model_dump() for s in c.sources],
            conflicting=c.conflicting
        )
        db.add(claim_record)
        
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Failed to save report: {e}")
        
    return str(report_id)
