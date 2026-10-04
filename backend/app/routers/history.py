import json
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Response
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api", tags=["history"])


def _row_to_dict(row):
    return {
        "id": row["id"],
        "analysis_type": row["analysis_type"],
        "input_text": row["input_text"],
        "input_image": row["input_image"],
        "verdict": row["verdict"],
        "confidence": row["confidence"],
        "signals": json.loads(row["signals"] or "[]"),
        "evidence": json.loads(row["evidence"] or "[]"),
        "created_at": row["created_at"],
    }


@router.get("/history")
def list_history(
    type: str | None = None,
    search: str | None = None,
    user=Depends(get_current_user)
):
    rows = models.get_analyses_by_user(user["id"], limit=100, analysis_type=type, search=search)
    return [_row_to_dict(r) for r in rows]


@router.get("/history/export/csv")
def export_history_csv(user=Depends(get_current_user)):
    rows = models.get_analyses_by_user(user["id"], limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Type", "Input", "Verdict", "Confidence", "Timestamp"])
    for r in rows:
        writer.writerow([r["id"], r["analysis_type"], r["input_text"] or r["input_image"], r["verdict"], r["confidence"], r["created_at"]])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=verifyengine_history.csv"}
    )


@router.get("/history/{analysis_id}")
def get_history_item(analysis_id: int, user=Depends(get_current_user)):
    row = models.get_analysis_by_id(analysis_id, user["id"])
    if not row:
        raise HTTPException(404, "Analysis not found")
    return _row_to_dict(row)


@router.delete("/history/{analysis_id}")
def delete_history_item(analysis_id: int, user=Depends(get_current_user)):
    row = models.get_analysis_by_id(analysis_id, user["id"])
    if not row:
        raise HTTPException(404, "Analysis not found")
    models.delete_analysis(analysis_id, user["id"])
    return {"status": "deleted", "id": analysis_id}


@router.get("/share/{analysis_id}")
def get_shared_analysis(analysis_id: int):
    """Public shareable link endpoint for a verification result."""
    row = models.get_analysis_by_id(analysis_id)
    if not row:
        raise HTTPException(404, "Shared analysis report not found")
    return _row_to_dict(row)
