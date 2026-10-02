from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from ..security import hash_password, verify_password, create_access_token
from ..deps import get_current_user
from .. import models

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    if models.get_user_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    uid = models.create_user(body.name, body.email, hash_password(body.password))
    return TokenResponse(access_token=create_access_token(uid), name=body.name)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = models.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return TokenResponse(access_token=create_access_token(user["id"]), name=user["name"])


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse(id=user["id"], name=user["name"], email=user["email"],
                        is_admin=bool(user["is_admin"]))
