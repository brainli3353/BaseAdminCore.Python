"""JWT 签发/校验（python-jose，双 token：access + refresh）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from src.core.config import get_settings

ALGORITHM = "HS256"


def _options():
    return get_settings().jwt


def create_token(
    claims: dict[str, Any],
    expires_hours: int | None = None,
    token_type: str = "access",
) -> str:
    opts = _options()
    hours = expires_hours if expires_hours is not None else opts.expire_hours
    now = datetime.now(UTC)
    payload: dict[str, Any] = dict(claims)
    payload.update(
        {
            "iss": opts.issuer,
            "aud": opts.audience,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=hours)).timestamp()),
            "typ": token_type,
        }
    )
    return jwt.encode(payload, opts.secret, algorithm=ALGORITHM)


def create_access_token(claims: dict[str, Any]) -> str:
    return create_token(claims, token_type="access")


def create_refresh_token(claims: dict[str, Any]) -> str:
    return create_token(claims, _options().refresh_token_expire_hours, token_type="refresh")


def decode_token(token: str) -> dict[str, Any]:
    opts = _options()
    return jwt.decode(token, opts.secret, algorithms=[ALGORITHM], issuer=opts.issuer, audience=opts.audience)


def verify_token(token: str) -> dict[str, Any]:
    try:
        return decode_token(token)
    except JWTError as exc:
        from src.core.exceptions import UnauthorizedException

        raise UnauthorizedException(msg="登录状态无效或已过期") from exc
