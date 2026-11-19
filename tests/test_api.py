import pyotp
from starlette.testclient import TestClient

from src.web.app import create_app


def _login(client: TestClient) -> str:
    first = client.post("/api/auth/login", json={"account": "admin", "password": "Admin@123"})
    data = first.json()["data"]
    code = pyotp.TOTP(data["secret"]).now()
    second = client.post("/api/auth/login/otp", json={"challengeId": data["challengeId"], "code": code})
    return second.json()["data"]


def test_authenticated_api_surface():
    app = create_app()
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        endpoints = [
            "/api/sysUser/page",
            "/api/sysRole/page",
            "/api/sysMenu/tree",
            "/api/sysOrg/tree",
            "/api/sysPos/page",
            "/api/sysDictType/page",
            "/api/sysConfig/page",
            "/api/sysLogOp/page",
            "/api/sysLogLogin/page",
            "/api/sysJob/page",
            "/api/sysFile/page",
            "/api/sysNotice/page",
            "/api/sysTenant/page",
            "/api/sysOpenAccess/page",
            "/api/sysEnum/typeList",
            "/api/sysServer/runtime",
            "/api/sysServer/hardware",
            "/api/sysServer/nodes",
            "/api/sysDatabase/tables",
            "/api/sysCodeGen/tables",
            "/api/sysPrint/page",
            "/api/sysSerial/page",
            "/api/sysLocalization/cultures",
            "/api/onlineUser/list",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200, endpoint
            assert response.json()["code"] == 0, (endpoint, response.json())


def test_unauthorized_api_is_401():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/sysUser/page")
        assert response.status_code == 401
