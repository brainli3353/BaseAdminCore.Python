import pyotp
from starlette.testclient import TestClient

from src.web.app import create_app


def test_two_phase_login_and_me():
    app = create_app()
    with TestClient(app) as client:
        first = client.post("/api/auth/login", json={"account": "admin", "password": "Admin@123"})
        body = first.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["bindRequired"] is True

        code = pyotp.TOTP(data["secret"]).now()
        second = client.post("/api/auth/login/otp", json={"challengeId": data["challengeId"], "code": code})
        assert second.status_code == 200
        token = second.json()["data"]
        assert token
        assert second.headers.get("X-Refresh-Token")

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        me_body = me.json()
        assert me_body["code"] == 0
        assert me_body["data"]["account"] == "admin"

        headers = {"Authorization": f"Bearer {token}"}
        menu = client.get("/api/sysMenu/user", headers=headers)
        assert menu.json()["code"] == 0
        names = [node["name"] for node in menu.json()["data"]]
        assert "dashboard" in names

        dict_data = client.get("/api/sysDictData/list?code=account_status", headers=headers)
        assert dict_data.json()["code"] == 0
        assert len(dict_data.json()["data"]) == 5
