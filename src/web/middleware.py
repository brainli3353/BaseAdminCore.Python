"""中间件：TraceId / 全局异常统一出口。"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.constants import ErrorCodes
from src.core.exceptions import AppException
from src.core.json import AdminJSONResponse
from src.core.responses import fail

logger = logging.getLogger("admincore")

WHITELIST = {
    "/api/auth/login",
    "/api/auth/login/otp",
    "/api/auth/me",
    "/api/auth/logout",
    "/api/sysMenu/user",
    "/api/sysMenu/tree",
    "/api/sysDictData/list",
    "/api/sysFile/upload",
    "/api/sysFile/download",
    "/api/sysUser/updatePassword",
    "/api/sysColumnCustom/get",
    "/api/sysColumnCustom/store",
    "/api/sysColumnCustom/reset",
    "/api/sysLocalization/cultures",
    "/api/app/info",
}


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response


class PermissionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if not path.startswith("/api/") or path in WHITELIST:
            return await call_next(request)
        token = request.query_params.get("access_token")
        authorization = request.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        if not token:
            return AdminJSONResponse(content=fail("未登录", 401, "common.unauthorized"), status_code=401)
        from src.core.auth.jwt import verify_token

        try:
            payload = verify_token(token)
        except Exception:
            return AdminJSONResponse(content=fail("登录状态无效", 401, "common.unauthorized"), status_code=401)
        if not payload.get("is_super"):
            permission = path[len("/api/"):]
            user_id = payload.get("uid")
            if user_id is not None and not await self._has_permission(int(user_id), permission):
                return AdminJSONResponse(
                    content=fail("无权限", 403, "common.forbidden"), status_code=403
                )
        return await call_next(request)

    async def _has_permission(self, user_id: int, permission: str) -> bool:
        from src.core.cache.cache_setup import get_cache_service
        from src.core.db.database import get_session_factory
        from src.core.services.menu_perm_service import MenuPermService

        factory = get_session_factory()
        session = factory()
        try:
            permissions = await MenuPermService(session, get_cache_service()).get_permissions(user_id)
        finally:
            await session.close()
        return permission in permissions


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AppException as exc:
            if exc.http_status == 200:
                return AdminJSONResponse(
                    content=fail(exc.msg, exc.code, exc.err_code, exc.data), status_code=200
                )
            return AdminJSONResponse(
                content=fail(exc.msg, exc.code, exc.err_code, exc.data), status_code=exc.http_status
            )
        except Exception:  # noqa: BLE001
            trace_id = getattr(request.state, "trace_id", None)
            logger.exception("未处理异常 trace_id=%s", trace_id)
            return AdminJSONResponse(
                content=fail("系统内部错误", ErrorCodes.ServerError, "common.server_error"),
                status_code=200,
            )
