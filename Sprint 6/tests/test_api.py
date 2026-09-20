from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analytics():
    r = client.get("/api/analytics")
    assert r.status_code == 200
    assert "overall" in r.json()

def test_dashboard():
    r = client.get("/")
    assert r.status_code == 200
    assert "ChatBiz" in r.text
