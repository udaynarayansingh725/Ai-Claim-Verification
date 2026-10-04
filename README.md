# Claim Verification & AI-Generated Content Detection Engine

[![Live Web Application](https://img.shields.io/badge/Live_Demo-https%3A%2F%2Fai--claim--verification.onrender.com-brightgreen?style=for-the-badge&logo=render)](https://ai-claim-verification.onrender.com/)

🌐 **Live Demo Application:** [https://ai-claim-verification.onrender.com/](https://ai-claim-verification.onrender.com/)

Combines three verification & detection tools in one modern web app:
1. **Claim Verification** — claim → keywords extraction → evidence retrieval → cross-verification → verdict (SUPPORTED / REFUTED / NOT ENOUGH INFO)
2. **AI Text Detection** — likelihood score with explainable signals (burstiness, lexical diversity, repetition, connective density)
3. **AI Image Detection** — likelihood score with explainable signals (EXIF metadata, Error Level Analysis, FFT frequency spectrum, saturation stats)

> Gives a **first-level, understandable assessment** — not a replacement for expert human fact-checking.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/udaynarayansingh725/Ai-Claim-Verification)

---

## 🌐 Live Web Application
- **URL:** [https://ai-claim-verification.onrender.com/](https://ai-claim-verification.onrender.com/)
- **Demo Credentials:**
  - **Email:** `admin@example.com`
  - **Password:** `admin123`

---

## Tech Stack
- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript (single page application, served by FastAPI)
- **Backend:** Python 3.10+ + FastAPI + Uvicorn
- **Database:** SQLite (default, zero setup). `database/schema.sql` included for MySQL/PostgreSQL.
- **Auth:** JWT tokens, PBKDF2 password hashing (stdlib only)
- **Testing:** Pytest

---

## How to Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python run.py
   ```
   *Or specify a custom port:*
   ```bash
   python run.py 8080
   ```

3. Open **http://127.0.0.1:8000** (or **http://127.0.0.1:8080**) in your browser.

4. Default admin account:
   - **Email:** `admin@example.com`
   - **Password:** `admin123`

---

## Optional: Live Evidence Search (NewsAPI)
Copy `.env.example` to `.env` and set `NEWSAPI_KEY`:
```env
NEWSAPI_KEY=your_key_here
```
Without a key, the built-in evidence knowledge base is used offline.

---

## Deployment Guide

### Live Deployment
The application is deployed live on Render:
👉 **[https://ai-claim-verification.onrender.com/](https://ai-claim-verification.onrender.com/)**

### Deploying Your Own Copy on Render
1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
3. Select your GitHub repository (`Ai-Claim-Verification`).
4. Select the **Free ($0 / month)** instance type.
5. Set:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
6. Click **Create Web Service**.

---

## Project Structure
```
Ai-Claim-Verification/
├── run.py                  # Entry point
├── main.py                 # Root convenience runner
├── requirements.txt
├── Procfile                # Heroku / Render / Railway deployment
├── Dockerfile              # Docker container deployment
├── render.yaml             # Render Blueprint configuration
├── runtime.txt             # Python runtime specification
├── .env.example
├── database/
│   └── schema.sql          # MySQL/PostgreSQL schema
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app + static mount
│   │   ├── config.py       # Configuration & env loader
│   │   ├── db.py           # SQLite connection layer
│   │   ├── security.py     # JWT + PBKDF2 password hashing
│   │   ├── models.py       # Database query helpers
│   │   ├── schemas.py      # Pydantic request & response schemas
│   │   ├── deps.py         # Auth dependency injection
│   │   ├── services/
│   │   │   ├── claim_service.py      # Claim verification engine
│   │   │   ├── text_ai_service.py    # AI text likelihood detector
│   │   │   └── image_ai_service.py   # AI image ELA & FFT detector
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── claims.py
│   │       ├── detect.py
│   │       └── history.py
│   └── static/
│       ├── index.html
│       ├── css/styles.css
│       └── js/app.js
└── tests/
    └── test_api.py         # Comprehensive unit, negative & security tests
```

---

## Testing
Run the automated test suite:
```bash
python -m pytest tests/ -v
```
