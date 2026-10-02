-- Schema for MySQL / PostgreSQL (SQLite DDL is created automatically by the app)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    analysis_type VARCHAR(20) NOT NULL,          -- claim | text | image
    input_text TEXT,
    input_image VARCHAR(255),
    verdict VARCHAR(50),
    confidence REAL,
    signals TEXT,                                -- JSON array of explanation signals
    evidence TEXT,                               -- JSON array of evidence items (claims)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
