from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import STATIC_DIR
from .db import init_db
from .security import hash_password
from . import models
from .routers import auth, claims, detect, history, admin

app = FastAPI(title="Claim Verification & AI Content Detection Engine",
              description="First-level claim checking + AI text/image detection",
              version="2.0.0")


@app.get("/api/health")
def health():
    return {"status": "ok"}


for r in (auth.router, claims.router, detect.router, history.router, admin.router):
    app.include_router(r)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


def bootstrap():
    """Create tables and seed the default admin account."""
    init_db()
    if not models.get_user_by_email("admin@example.com"):
        models.create_user("Admin", "admin@example.com", hash_password("admin123"), is_admin=1)


bootstrap()
