from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.db.models import Report
import uuid

reports_router = APIRouter()

@reports_router.get("/reports/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    try:
        query = select(Report).where(Report.id == report_uuid).options(selectinload(Report.claims))
        result = await db.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        return {
            "id": str(report.id),
            "input_text": report.input_text,
            "source_url": report.source_url,
            "overall_score": report.overall_score,
            "ai_text_probability": report.ai_text_probability,
            "created_at": report.created_at,
            "claims": [
                {
                    "id": str(c.id),
                    "claim_text": c.claim_text,
                    "verdict": c.verdict,
                    "confidence": c.confidence,
                    "reasoning": c.reasoning,
                    "sources": c.sources,
                    "conflicting": c.conflicting
                } for c in report.claims
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

@reports_router.delete("/reports/{report_id}")
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db)):
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    try:
        query = select(Report).where(Report.id == report_uuid)
        result = await db.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        await db.delete(report)
        await db.commit()
        
        return {"message": "Report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
