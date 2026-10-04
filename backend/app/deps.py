from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .security import decode_access_token
from . import models

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    x_api_key: str | None = Header(None, alias="X-API-Key")
):
    # 1. API Key Authentication
    if x_api_key:
        user = models.get_user_by_api_key(x_api_key)
        if user:
            return user
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API Key")

    # 2. JWT Bearer Token Authentication
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    
    payload = decode_access_token(creds.credentials)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
        
    user = models.get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
        
    return user
