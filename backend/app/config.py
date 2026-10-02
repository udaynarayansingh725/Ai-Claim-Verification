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

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24          # 1 day

_raw_db = os.getenv("DB_PATH", str(PROJECT_ROOT / "app.db"))
if _raw_db == ":memory:":
    DB_PATH = ":memory:"
elif Path(_raw_db).is_absolute():
    DB_PATH = _raw_db
else:
    DB_PATH = str(PROJECT_ROOT / _raw_db)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
STATIC_DIR = BASE_DIR / "static"

# Claim verification tuning
SUPPORT_THRESHOLD = 0.45      # min similarity to mark SUPPORTED
REFUTE_CUE_BONUS = 0.25       # boost when contradiction cues found
MAX_EVIDENCE = 5
