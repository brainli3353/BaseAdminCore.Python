from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth.jwt import verify_token
from src.core.cache.cache_setup import get_cache_service
from src.core.constants import CacheConst
from src.core.db.context import UserContext, set_current_user
from src.core.db.database import get_session
from src.core.exceptions import UnauthorizedException
from src.core.services.auth.auth_service import AuthService
from src.core.services.auth.user_token_state import UserTokenStateProvider
from src.core.services.config_service import SysConfigService
from src.core.services.login_log_service import SysLogLoginService
from src.core.services.user_service import SysUserService

DbDep = Annotated[AsyncSession, Depends(get_session)]


def get_bearer_token(request: Request, authorization: Annotated[str | None, Header()] = None) -> str | None:
    token = request.query_params.get("access_token")
    if token:
        return token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def get_optional_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> UserContext | None:
    token = get_bearer_token(request, authorization)
    if not token:
        return None
    try:
        payload = verify_token(token)
    except Exception:
        return None
    return _context_from_payload(payload)


def _context_from_payload(payload: dict) -> UserContext:
    role_ids = payload.get("rids") or ()
    if isinstance(role_ids, str):
        role_ids = [int(x) for x in role_ids.split(",") if x]
    return UserContext(
        user_id=int(payload.get("uid")) if payload.get("uid") is not None else None,
        account=payload.get("acct"),
        real_name=payload.get("rn"),
        org_id=int(payload["org"]) if payload.get("org") is not None else None,
        tenant_id=int(payload["tid"]) if payload.get("tid") is not None else None,
        token_version=int(payload.get("tv") or 0),
        role_ids=tuple(int(x) for x in role_ids),
        is_super_admin=bool(payload.get("is_super")),
    )


async def require_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> UserContext:
    token = get_bearer_token(request, authorization)
    if not token:
        raise UnauthorizedException()
    payload = verify_token(token)
    user = _context_from_payload(payload)
    if user.user_id is None:
        raise UnauthorizedException()

    cache = get_cache_service()
    if await cache.exists(f"sys_token_blacklist:{token}"):
        raise UnauthorizedException("Token 已失效,请重新登录")

    claim_version = user.token_version
    version_key = f"{CacheConst.KeyUserToken}{user.user_id}"
    current_raw = await cache.get(version_key)
    current = int(current_raw) if current_raw else 0
    if current <= 0:
        state = await UserTokenStateProvider(session).get_user_state(user.user_id)
        if state is None:
            raise UnauthorizedException("用户不存在")
        if state.is_disabled:
            raise UnauthorizedException("账号已停用")
        if not state.tenant_valid:
            raise UnauthorizedException("租户已停用或已过期")
        current = state.token_version
        await cache.set(version_key, str(current))
    if current != claim_version:
        raise UnauthorizedException("Token 已失效,请重新登录")

    set_current_user(user)
    request.state.user = user
    return user


UserDep = Annotated[UserContext, Depends(require_user)]


def require_perm(permission: str):
    async def dependency(
        user: Annotated[UserContext, Depends(require_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> UserContext:
        if user.is_super_admin:
            return user
        from src.core.services.menu_perm_service import MenuPermService

        permissions = await MenuPermService(session, get_cache_service()).get_permissions(user.user_id or 0)
        if permission not in permissions:
            from src.core.exceptions import ForbiddenException

            raise ForbiddenException()
        return user

    return dependency


def get_auth_service(session: Annotated[AsyncSession, Depends(get_session)]) -> AuthService:
    cache = get_cache_service()
    config_service = SysConfigService(session, cache)
    return AuthService(
        session=session,
        cache=cache,
        config_service=config_service,
        login_log_service=SysLogLoginService(session),
        user_service=SysUserService(session, cache),
        token_state_provider=UserTokenStateProvider(session),
    )
