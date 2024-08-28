import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_lookup():
    item_id = 1
    response = client.get(f"/lookup/{item_id}")
    assert response.status_code == 200
    assert response.json() == {"item_id": item_id, "name": "Item Name"}

def test_history():
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == [{"event": "Event 1"}, {"event": "Event 2"}]

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json() == {"message": "Metrics are available"}
