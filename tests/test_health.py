
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

def test_openapi_schema_endpoint():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "paths" in response.json()


def test_unknown_endpoint_returns_404():
    response = client.get("/this-endpoint-does-not-exist")

    assert response.status_code == 404
