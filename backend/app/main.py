import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import STATIC_DIR, ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD
from .db import init_db
from .security import hash_password
from . import models
from .routers import auth, claims, detect, history, admin, eval

app_start_time = time.time()

app = FastAPI(
    title="Claim Verification & AI Content Detection Engine",
    description="Production-grade claim verification, AI text detection, AI image forensics & API platform",
    version="2.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "2.5.0",
        "uptime_seconds": round(time.time() - app_start_time, 2),
        "database": "connected",
        "docs_url": "/docs"
    }


for r in (auth.router, claims.router, detect.router, history.router, admin.router, eval.router):
    app.include_router(r)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


def bootstrap():
    """Create tables and seed the default admin account from environment variables."""
    init_db()
    if not models.get_user_by_email(ADMIN_EMAIL):
        models.create_user(ADMIN_NAME, ADMIN_EMAIL, hash_password(ADMIN_PASSWORD), is_admin=1)


bootstrap()
