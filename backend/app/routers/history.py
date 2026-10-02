import json
from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/history", tags=["history"])


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


@router.get("")
def list_history(user=Depends(get_current_user)):
    rows = models.get_analyses_by_user(user["id"])
    return [_row_to_dict(r) for r in rows]


@router.get("/{analysis_id}")
def get_history_item(analysis_id: int, user=Depends(get_current_user)):
    row = models.get_analysis_by_id(analysis_id, user["id"])
    if not row:
        raise HTTPException(404, "Analysis not found")
    return _row_to_dict(row)
