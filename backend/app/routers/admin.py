from fastapi import APIRouter, Depends, HTTPException, status
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(user=Depends(get_current_user)):
    if not user["is_admin"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return user


@router.get("/stats")
def get_stats(user=Depends(verify_admin)):
    return models.get_admin_stats()


@router.get("/users")
def get_users(user=Depends(verify_admin)):
    rows = models.get_all_users()
    return [dict(r) for r in rows]
