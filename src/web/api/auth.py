from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.exceptions import AppException
from src.core.json import AdminJSONResponse
from src.core.responses import success
from src.core.services.auth.auth_service import AuthService
from src.core.services.auth.dto import LoginInput, LoginOtpInput
from src.core.services.menu_perm_service import MenuPermService
from src.web.deps import UserDep, get_auth_service, get_bearer_token, get_cache_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _error_message(result) -> str:
    return result.error or "登录失败"


@router.post("/login")
async def login(
    input: LoginInput,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    result = await service.login(input.account, input.password, _remote_addr(request))
    if not result.success:
        raise AppException(result.error_code, _error_message(result), code=1, http_status=401)
    if result.token:
        return _token_response(result)
    return AdminJSONResponse(content=success(result.data and _output_dict(result.data)))


@router.post("/login/otp")
async def login_otp(
    input: LoginOtpInput,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    result = await service.login_otp(input.challenge_id, input.code, _remote_addr(request))
    if not result.success:
        raise AppException(result.error_code, _error_message(result), code=1, http_status=401)
    return _token_response(result)


def _token_response(result):
    headers = {}
    if result.password_expired:
        headers["X-Password-Expired"] = "true"
    if result.refresh_token:
        headers["X-Refresh-Token"] = result.refresh_token
    return AdminJSONResponse(content=success(result.token), headers=headers)


@router.get("/me")
async def me(
    user: UserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    permissions = []
    if not user.is_super_admin:
        permissions = sorted(await MenuPermService(session, get_cache_service()).get_permissions(user.user_id or 0))
    return success(
        {
            "userId": user.user_id,
            "account": user.account,
            "realName": user.real_name,
            "accountType": 999 if user.is_super_admin else 777,
            "permissions": permissions,
        }
    )


@router.post("/logout")
async def logout(
    request: Request,
    user: UserDep,
    service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
):
    token = get_bearer_token(request, authorization)
    await service.logout(f"Bearer {token}" if token else None, _remote_addr(request))
    return success()


def _output_dict(output):
    return {
        "challengeId": output.challenge_id,
        "bindRequired": output.bind_required,
        "otpauthUri": output.otpauth_uri,
        "secret": output.secret,
    }


def _remote_addr(request: Request) -> str | None:
    return request.client.host if request.client else None
