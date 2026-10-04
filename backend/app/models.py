"""Row -> dict helpers for database interactions."""
from . import db


# ---------- users ----------
def create_user(name, email, password_hash, is_admin=0, api_key=None):
    return db.execute(
        "INSERT INTO users (name, email, password_hash, is_admin, api_key) VALUES (?,?,?,?,?)",
        (name, email.lower().strip(), password_hash, is_admin, api_key),
    )


def get_user_by_email(email):
    return db.query("SELECT * FROM users WHERE email = ?", (email.lower().strip(),), one=True)


def get_user_by_id(user_id):
    return db.query("SELECT * FROM users WHERE id = ?", (user_id,), one=True)


def get_user_by_api_key(api_key):
    return db.query("SELECT * FROM users WHERE api_key = ?", (api_key.strip(),), one=True)


def update_user_api_key(user_id, api_key):
    db.execute("UPDATE users SET api_key = ? WHERE id = ?", (api_key, user_id))
    return api_key


def get_all_users():
    return db.query("SELECT id, name, email, is_admin, api_key, created_at FROM users ORDER BY id DESC")


# ---------- analyses ----------
def create_analysis(user_id, analysis_type, input_text=None, input_image=None,
                    verdict=None, confidence=None, signals="[]", evidence="[]"):
    return db.execute(
        """INSERT INTO analyses
           (user_id, analysis_type, input_text, input_image, verdict, confidence, signals, evidence)
           VALUES (?,?,?,?,?,?,?,?)""",
        (user_id, analysis_type, input_text, input_image, verdict, confidence, signals, evidence),
    )


def get_analyses_by_user(user_id, limit=100, analysis_type=None, search=None):
    sql = "SELECT * FROM analyses WHERE user_id = ?"
    params = [user_id]
    
    if analysis_type and analysis_type != "all":
        sql += " AND analysis_type = ?"
        params.append(analysis_type)
        
    if search:
        sql += " AND (input_text LIKE ? OR verdict LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return db.query(sql, tuple(params))


def get_analysis_by_id(analysis_id, user_id=None):
    if user_id:
        return db.query("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id), one=True)
    return db.query("SELECT * FROM analyses WHERE id = ?", (analysis_id,), one=True)


def delete_analysis(analysis_id, user_id):
    return db.execute("DELETE FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id))


def get_admin_stats():
    total_users = db.query("SELECT COUNT(*) as count FROM users", one=True)["count"]
    total_analyses = db.query("SELECT COUNT(*) as count FROM analyses", one=True)["count"]
    claim_count = db.query("SELECT COUNT(*) as count FROM analyses WHERE analysis_type = 'claim'", one=True)["count"]
    text_count = db.query("SELECT COUNT(*) as count FROM analyses WHERE analysis_type = 'text'", one=True)["count"]
    image_count = db.query("SELECT COUNT(*) as count FROM analyses WHERE analysis_type = 'image'", one=True)["count"]
    
    # Verdict Distribution
    verdicts = db.query("""
        SELECT verdict, COUNT(*) as count 
        FROM analyses 
        GROUP BY verdict 
        ORDER BY count DESC
    """)
    
    return {
        "total_users": total_users,
        "total_analyses": total_analyses,
        "claim_count": claim_count,
        "text_count": text_count,
        "image_count": image_count,
        "verdict_distribution": [dict(v) for v in verdicts]
    }
