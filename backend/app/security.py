"""Password hashing + JWT using only the Python standard library.

Passwords: PBKDF2-HMAC-SHA256, 100k iterations, random salt.
Tokens: HS256 JWT (header.payload.signature, base64url).
"""
import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from .config import SECRET_KEY, TOKEN_EXPIRE_MINUTES

PBKDF2_ITERATIONS = 100_000


# ---------- password hashing ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False


# ---------- base64url helpers ----------
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


# ---------- JWT ----------
def create_access_token(user_id: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "exp": int(time.time()) + TOKEN_EXPIRE_MINUTES * 60,
    }
    signing_input = f"{_b64url_encode(json.dumps(header).encode())}.{_b64url_encode(json.dumps(payload).encode())}"
    sig = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(sig)}"


def decode_access_token(token: str):
    """Return payload dict, or None if invalid/expired."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_decode(sig_b64), expected):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except (ValueError, json.JSONDecodeError, base64.binascii.Error):
        return None
