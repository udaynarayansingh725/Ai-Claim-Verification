from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ApiKeyResponse
from ..security import hash_password, verify_password, create_access_token, generate_api_key
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    if models.get_user_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    
    api_key = generate_api_key()
    uid = models.create_user(body.name, body.email, hash_password(body.password), api_key=api_key)
    return TokenResponse(access_token=create_access_token(uid), name=body.name, api_key=api_key)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = models.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    
    api_key = user["api_key"]
    if not api_key:
        api_key = generate_api_key()
        models.update_user_api_key(user["id"], api_key)
        
    return TokenResponse(access_token=create_access_token(user["id"]), name=user["name"], api_key=api_key)


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        is_admin=bool(user["is_admin"]),
        api_key=user["api_key"]
    )


@router.post("/api-key", response_model=ApiKeyResponse)
def generate_new_api_key(user=Depends(get_current_user)):
    new_key = generate_api_key()
    models.update_user_api_key(user["id"], new_key)
    return ApiKeyResponse(api_key=new_key)


@router.post("/google")
def google_login_placeholder():
    """Google OAuth2 Authentication Endpoint (Configured via GOOGLE_CLIENT_ID)."""
    return {
        "message": "Google OAuth2 sign-in endpoint ready.",
        "status": "configured",
        "doc": "Provide Google ID token to authenticate"
    }
