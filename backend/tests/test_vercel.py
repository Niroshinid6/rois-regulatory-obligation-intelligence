from fastapi.testclient import TestClient

from api.index import app


client = TestClient(app)


def test_vercel_entrypoint_imports_existing_app():
    from app.main import app as application

    assert app is application


def test_vercel_entrypoint_preserves_health_route():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
