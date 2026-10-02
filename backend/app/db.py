"""SQLite connection layer (stdlib sqlite3).

Swap note: to use MySQL/PostgreSQL, import database/schema.sql and replace
this module's queries with your driver of choice (same table/column names).
"""
import sqlite3
from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL,               -- claim | text | image
    input_text TEXT,
    input_image TEXT,
    verdict TEXT,
    confidence REAL,
    signals TEXT,                              -- JSON
    evidence TEXT,                             -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def query(sql, params=(), one=False):
    conn = get_conn()
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id
