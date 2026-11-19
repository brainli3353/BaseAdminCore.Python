from starlette.testclient import TestClient

from src.web.app import create_app


def test_health_and_login_challenge():
    app = create_app()
    with TestClient(app) as client:
        live = client.get("/health/live")
        assert live.status_code == 200

        resp = client.post("/api/auth/login", json={"account": "admin", "password": "Admin@123"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["challengeId"]
        assert data["bindRequired"] is True
        assert data["secret"]


def test_login_wrong_password():
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/api/auth/login", json={"account": "admin", "password": "wrong"})
        assert resp.status_code == 401
        assert resp.json()["code"] != 0
