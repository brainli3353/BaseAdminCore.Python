from starlette.testclient import TestClient

from src.web.app import create_app


def test_spa_served_and_api_prefixed():
    app = create_app()
    with TestClient(app) as client:
        index = client.get("/")
        assert index.status_code == 200
        assert "id=\"app\"" in index.text

        login = client.get("/login")
        assert login.status_code == 200
        assert "id=\"app\"" in login.text

        live = client.get("/health/live")
        assert live.status_code == 200

        missing_api = client.get("/api/does-not-exist")
        assert missing_api.status_code == 401
