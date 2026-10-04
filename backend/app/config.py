import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
PROJECT_ROOT = BASE_DIR.parent                              # repo root


def _load_env():
    """Tiny .env loader (no external dependency)."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

# Security & Secrets
SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-12345")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24          # 1 day

# Admin Credentials (configured via environment variables)
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Database Configuration (PostgreSQL supported via DATABASE_URL or SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "")
_raw_db = os.getenv("DB_PATH", str(PROJECT_ROOT / "app.db"))
if _raw_db == ":memory:":
    DB_PATH = ":memory:"
elif Path(_raw_db).is_absolute():
    DB_PATH = _raw_db
else:
    DB_PATH = str(PROJECT_ROOT / _raw_db)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
STATIC_DIR = BASE_DIR / "static"
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Rate Limits
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# Claim verification tuning
SUPPORT_THRESHOLD = 0.45      # min similarity to mark SUPPORTED
REFUTE_CUE_BONUS = 0.25       # boost when contradiction cues found
MAX_EVIDENCE = 5
