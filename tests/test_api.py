"""Unit / integration / negative / security tests (per project evaluation plan)."""
import os
os.environ["DB_PATH"] = ":memory:"
# NOTE: :memory: gives each connection a fresh DB, so tests use a temp file instead.
import tempfile, json
os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "test_verifyengine.db")
if os.path.exists(os.environ["DB_PATH"]):
    os.remove(os.environ["DB_PATH"])

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def auth(email, name="Test User", password="secret123"):
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


# ---------- auth ----------
def test_register_login_me():
    h = auth("user1@test.com")
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 200 and r.json()["email"] == "user1@test.com"

    r = client.post("/api/auth/login", json={"email": "user1@test.com", "password": "secret123"})
    assert r.status_code == 200
    # negative: wrong password
    r = client.post("/api/auth/login", json={"email": "user1@test.com", "password": "wrong"})
    assert r.status_code == 401

def test_duplicate_email_rejected():
    auth("dup@test.com")
    r = client.post("/api/auth/register", json={"name": "X", "email": "dup@test.com", "password": "secret1"})
    assert r.status_code == 409


# ---------- security: protected routes ----------
def test_unauthorized_blocked():
    assert client.post("/api/verify-claim", json={"claim": "Water boils at 100 degrees"}).status_code in (401, 403)
    assert client.post("/api/detect-text", json={"text": "hello world " * 10}).status_code in (401, 403)
    assert client.get("/api/history").status_code in (401, 403)


# ---------- claim verification ----------
def test_verify_claim_supported():
    h = auth("claim1@test.com")
    r = client.post("/api/verify-claim", json={"claim": "The Earth orbits the Sun once per year"},
                    headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("SUPPORTED", "NOT ENOUGH INFO")
    assert body["confidence"] >= 0

def test_verify_claim_refuted():
    h = auth("claim2@test.com")
    r = client.post("/api/verify-claim",
                    json={"claim": "Humans use only 10 percent of their brains"}, headers=h)
    assert r.status_code == 200
    assert r.json()["verdict"] == "REFUTED"

def test_claim_too_short_rejected():
    h = auth("claim3@test.com")
    r = client.post("/api/verify-claim", json={"claim": "short"}, headers=h)
    assert r.status_code == 422


# ---------- AI text detection ----------
def test_detect_text_ai_like():
    h = auth("text1@test.com")
    ai_text = ("In today's digital age, it is important to note that technology plays a crucial role. "
               "Furthermore, it is important to note that innovation drives progress. Moreover, in conclusion, "
               "it is important to note that the landscape of change underscores the importance of growth. "
               "Overall, it is important to note that the world of tomorrow serves as a reminder of hope. "
               "Additionally, it is important to note that progress plays a vital role in society today.")
    r = client.post("/api/detect-text", json={"text": ai_text}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] > 0.5
    assert body["signals"]

def test_detect_text_too_short():
    h = auth("text2@test.com")
    r = client.post("/api/detect-text", json={"text": "tiny"}, headers=h)
    assert r.status_code == 422


# ---------- AI image detection ----------
def _make_jpeg(with_exif=True):
    from PIL import Image
    import io, numpy as np
    np.random.seed(42)
    data = (np.random.rand(128, 128, 3) * 255).astype(np.uint8)
    img = Image.fromarray(data)
    buf = io.BytesIO()
    if with_exif:
        exif = img.getexif()
        exif[0x010f] = "TestCamera"
        img.save(buf, "JPEG", exif=exif)
    else:
        img.save(buf, "JPEG")
    return buf.getvalue()

def test_detect_image_real():
    h = auth("img1@test.com")
    r = client.post("/api/detect-image", files={"file": ("photo.jpg", _make_jpeg(), "image/jpeg")},
                    headers=h)
    assert r.status_code == 200
    assert r.json()["verdict"] in ("Likely a real photograph", "Possibly AI-generated")

def test_detect_image_bad_type():
    h = auth("img2@test.com")
    r = client.post("/api/detect-image", files={"file": ("x.txt", b"hello", "text/plain")}, headers=h)
    assert r.status_code == 400

def test_detect_image_not_an_image():
    h = auth("img3@test.com")
    r = client.post("/api/detect-image",
                    files={"file": ("fake.png", b"not-an-image", "image/png")}, headers=h)
    assert r.status_code == 200
    assert r.json()["verdict"] == "Invalid image"


# ---------- history ----------
def test_history_saved():
    h = auth("hist@test.com")
    client.post("/api/verify-claim", json={"claim": "Water boils at 100 degrees at sea level"}, headers=h)
    r = client.get("/api/history", headers=h)
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1 and items[0]["analysis_type"] == "claim"
    item = client.get(f"/api/history/{items[0]['id']}", headers=h)
    assert item.status_code == 200

def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}
