import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

# Mock the logging configuration to avoid permission errors
@pytest.fixture(autouse=True)
def mock_logging():
    with patch('main.logging.basicConfig') as mock_logging:
        yield mock_logging

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "date" in response.json()
    assert "version" in response.json()
    assert "kubernetes" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
