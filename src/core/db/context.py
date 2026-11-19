"""请求级当前用户上下文（contextvars，异步安全）。"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from src.core.constants import ClaimsConst, DbConst


@dataclass(frozen=True)
class UserContext:
    user_id: int | None = None
    account: str | None = None
    real_name: str | None = None
    org_id: int | None = None
    tenant_id: int | None = None
    token_version: int = 0
    role_ids: tuple[int, ...] = ()
    is_super_admin: bool = False


_current_user: ContextVar[UserContext | None] = ContextVar("current_user", default=None)


def set_current_user(user: UserContext | None) -> None:
    _current_user.set(user)


def get_current_user() -> UserContext | None:
    return _current_user.get()


def current_user_id() -> int | None:
    return _current_user.get().user_id if _current_user.get() else None


def current_tenant_id() -> int | None:
    user = _current_user.get()
    if user is None or user.is_super_admin:
        return user.tenant_id if user else None
    return user.tenant_id


def is_super_admin() -> bool:
    user = _current_user.get()
    return bool(user and user.is_super_admin)


def ensure_user() -> UserContext:
    user = _current_user.get()
    if user is None or user.user_id is None:
        from src.core.exceptions import UnauthorizedException

        raise UnauthorizedException()
    return user


def default_tenant_id() -> int:
    user = _current_user.get()
    if user and user.tenant_id is not None:
        return user.tenant_id
    return DbConst.DefaultTenantId


__all__ = [
    "UserContext",
    "ClaimsConst",
    "set_current_user",
    "get_current_user",
    "current_user_id",
    "current_tenant_id",
    "is_super_admin",
    "ensure_user",
    "default_tenant_id",
]
