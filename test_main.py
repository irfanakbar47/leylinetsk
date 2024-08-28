from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "date": int(datetime.utcnow().timestamp()),  # Adjust this check according to your logic
        "version": "1.0.0",
        "kubernetes": False  # Adjust based on your environment
    }

# Add more tests similarly...
