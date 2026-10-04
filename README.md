# Claim Verification & AI-Generated Content Detection Engine

Combines three verification & detection tools in one modern web app:
1. **Claim Verification** — claim → keywords extraction → evidence retrieval → cross-verification → verdict (SUPPORTED / REFUTED / NOT ENOUGH INFO)
2. **AI Text Detection** — likelihood score with explainable signals (burstiness, lexical diversity, repetition, connective density)
3. **AI Image Detection** — likelihood score with explainable signals (EXIF metadata, Error Level Analysis, FFT frequency spectrum, saturation stats)

> Gives a **first-level, understandable assessment** — not a replacement for expert human fact-checking.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/udaynarayansingh725/Ai-Claim-Verification)

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

### Option 1: Deploy on Render
1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
3. Select your GitHub repository (`Ai-Claim-Verification`).
4. Set the following:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**.

*Alternatively, use Render Blueprints with the included `render.yaml`.*

### Option 2: Deploy on Railway
1. Go to [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this repository. Railway will automatically detect the `Procfile` / `Dockerfile` and deploy.

### Option 3: Deploy with Docker
```bash
docker build -t ai-claim-verification .
docker run -p 8000:8000 ai-claim-verification
```

---

## Project Structure
```
Ai-Claim-Verification/
├── run.py                  # Entry point
├── main.py                 # Root convenience runner
├── requirements.txt
├── Procfile                # Heroku / Render / Railway deployment
├── Dockerfile              # Docker container deployment
├── render.yaml             # Render Blueprint
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
