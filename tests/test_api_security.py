from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


client = TestClient(app)


def test_health_exposes_request_id_header() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.json()["auth_enabled"] is True


def test_protected_route_requires_api_key() -> None:
    response = client.get("/api/v1/tools/error/742")

    assert response.status_code == 401


def test_protected_route_accepts_demo_api_key() -> None:
    response = client.get(
        "/api/v1/tools/error/742",
        headers={"X-API-Key": get_settings().api_auth_token},
    )

    assert response.status_code == 200
    assert response.json()["error_code"] == "742"
