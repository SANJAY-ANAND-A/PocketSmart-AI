from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "PocketSmart AI"
    assert data["status"] == "online"
    assert data["currency"]["code"] == "INR"
    assert data["currency"]["symbol"] == "₹"


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["default_currency"] == "INR"
    assert data["currency_symbol"] == "₹"
