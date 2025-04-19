from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_predict_api():
    response = client.post("/predict", json={"text": "Login page fails"})
    assert response.status_code == 200
    data = response.json()
    assert "most_similar" in data
    assert "similarity_score" in data
