"""Row -> dict helpers (models are defined as DDL in db.py)."""
from . import db


# ---------- users ----------
def create_user(name, email, password_hash, is_admin=0):
    return db.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?,?,?,?)",
        (name, email.lower().strip(), password_hash, is_admin),
    )


def get_user_by_email(email):
    return db.query("SELECT * FROM users WHERE email = ?", (email.lower().strip(),), one=True)


def get_user_by_id(user_id):
    return db.query("SELECT * FROM users WHERE id = ?", (user_id,), one=True)


# ---------- analyses ----------
def create_analysis(user_id, analysis_type, input_text=None, input_image=None,
                    verdict=None, confidence=None, signals="[]", evidence="[]"):
    return db.execute(
        """INSERT INTO analyses
           (user_id, analysis_type, input_text, input_image, verdict, confidence, signals, evidence)
           VALUES (?,?,?,?,?,?,?,?)""",
        (user_id, analysis_type, input_text, input_image, verdict, confidence, signals, evidence),
    )


def get_analyses_by_user(user_id, limit=50):
    return db.query(
        "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    )


def get_analysis_by_id(analysis_id, user_id):
    return db.query(
        "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
        (analysis_id, user_id), one=True,
    )
