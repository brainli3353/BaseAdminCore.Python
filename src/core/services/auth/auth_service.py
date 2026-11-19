from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth.jwt import create_access_token, create_refresh_token
from src.core.cache.base import ICacheService
from src.core.config import get_settings
from src.core.constants import CacheConst, DbConst, ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_tenant import SysTenant
from src.core.entities.sys_user import SysUser, SysUserOtp
from src.core.security import otp_service
from src.core.security.cryptogram import decrypt, encrypt
from src.core.security.pbkdf2 import verify_password
from src.core.services.auth.challenge import LoginOtpChallenge
from src.core.services.auth.dto import LoginOutput, LoginResult
from src.core.services.auth.user_token_state import UserTokenStateProvider
from src.core.services.config_service import SysConfigService
from src.core.services.login_log_service import SysLogLoginService
from src.core.services.user_service import SysUserService

logger = logging.getLogger("admincore.auth")

CHALLENGE_TTL = 300
ERROR_WINDOW = 30 * 60
MAX_PASSWORD_ERRORS = 5
MAX_OTP_FAILS = 5
MAX_OTP_ERRORS = 10
MAX_ACCOUNT_LENGTH = 64
MAX_PASSWORD_LENGTH = 128
MAX_CODE_LENGTH = 8


def _error_key(account: str) -> str:
    return f"{CacheConst.KeyPasswordError}{account}"


def _otp_error_key(account: str) -> str:
    return f"{CacheConst.KeyOtpError}{account}"


def _challenge_key(challenge_id: int) -> str:
    return f"sys_login_otp_challenge:{challenge_id}"


def _blacklist_key(token: str) -> str:
    return f"sys_token_blacklist:{token}"


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        cache: ICacheService,
        config_service: SysConfigService,
        login_log_service: SysLogLoginService,
        user_service: SysUserService,
        token_state_provider: UserTokenStateProvider,
    ) -> None:
        self._user_repo = Repository(session, SysUser)
        self._otp_repo = Repository(session, SysUserOtp)
        self._tenant_repo = Repository(session, SysTenant)
        self._cache = cache
        self._config = config_service
        self._login_log = login_log_service
        self._user_service = user_service
        self._token_state = token_state_provider
        self._session = session

    async def login(self, account: str | None, password: str | None, remote_addr: str | None = None) -> LoginResult:
        account = (account or "").strip()
        if not account or not password:
            await self._write_login_log(account, None, False, "账号或密码错误", "login", remote_addr)
            return _fail(ErrorKeys.AuthLoginFailed, "账号或密码错误")
        if len(account) > MAX_ACCOUNT_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            await self._write_login_log(account, None, False, "账号或密码错误", "login", remote_addr)
            return _fail(ErrorKeys.AuthLoginFailed, "账号或密码错误")

        error_count = int(await self._cache.get(_error_key(account)) or 0)
        if error_count >= MAX_PASSWORD_ERRORS:
            await self._write_login_log(account, None, False, "登录失败次数过多,请 30 分钟后重试", "login", remote_addr)
            return _fail(ErrorKeys.AuthTooManyAttempts, "登录失败次数过多,请 30 分钟后重试")

        user = await self._user_repo.get_first(SysUser.account == account)
        if user is None or user.status != 0 or not verify_password(password, user.password):
            await self._cache.increment(_error_key(account), 1, ERROR_WINDOW)
            disabled = user is not None and user.status != 0
            await self._write_login_log(
                account, user.tenant_id if user else None, False,
                "账号已停用" if disabled else "账号或密码错误", "login", remote_addr,
            )
            if disabled:
                return _fail(ErrorKeys.AuthAccountDisabled, "账号已停用")
            return _fail(ErrorKeys.AuthLoginFailed, "账号或密码错误")

        tenant_error = await self._verify_tenant(user)
        if tenant_error is not None:
            await self._write_login_log(account, user.tenant_id, False, tenant_error, "login", remote_addr)
            return _fail(tenant_error, tenant_error)

        if not await self._is_otp_required():
            token, refresh, expired = await self._issue_tokens(user, remote_addr)
            return LoginResult(success=True, token=token, refresh_token=refresh, password_expired=expired)

        otp_row = await self._otp_repo.get_first(SysUserOtp.user_id == user.id, SysUserOtp.enabled == True)  # noqa: E712
        bind_required = otp_row is None
        if bind_required:
            pending = await self._otp_repo.get_first(SysUserOtp.user_id == user.id)
            pending_secret = _try_decrypt(pending.secret_cipher if pending else None)
            setup_secret = pending_secret or otp_service.generate_setup_secret()
            try:
                if pending is None:
                    await self._otp_repo.add(
                        SysUserOtp(
                            user_id=user.id,
                            secret_cipher=encrypt(setup_secret),
                            enabled=False,
                            tenant_id=user.tenant_id or DbConst.DefaultTenantId,
                        )
                    )
                elif pending_secret != setup_secret:
                    pending.secret_cipher = encrypt(setup_secret)
                    pending.enabled = False
                    await self._otp_repo.update(pending)
            except Exception:
                logger.warning("OTP pending 密钥落库失败", exc_info=True)
        else:
            try:
                setup_secret = decrypt(otp_row.secret_cipher)  # type: ignore[union-attr]
            except Exception:
                bind_required = True
                setup_secret = otp_service.generate_setup_secret()

        challenge_id = _next_challenge_id()
        await self._cache.set(
            _challenge_key(challenge_id),
            LoginOtpChallenge(user.id, user.account or "", setup_secret, bind_required, 0).to_json(),
            CHALLENGE_TTL,
        )
        output = LoginOutput(str(challenge_id), bind_required)
        if bind_required:
            output.otpauth_uri = _build_otpauth_uri(user.account or "", setup_secret)
            output.secret = setup_secret
        return LoginResult(success=True, data=output)

    async def login_otp(
        self, challenge_id: str | None, code: str | None, remote_addr: str | None = None
    ) -> LoginResult:
        if not challenge_id or not code:
            await self._write_login_log(None, None, False, "登录验证已过期,请重新登录", "login", remote_addr)
            return _fail(ErrorKeys.AuthChallengeExpired, "登录验证已过期,请重新登录")
        try:
            cid = int(challenge_id)
        except ValueError:
            cid = 0
        if cid <= 0:
            return _fail(ErrorKeys.AuthChallengeExpired, "登录验证已过期,请重新登录")
        if len(code) > MAX_CODE_LENGTH:
            await self._write_login_log(None, None, False, "校验码验证失败", "login", remote_addr)
            return _fail(ErrorKeys.AuthOtpVerifyFailed, "校验码验证失败")

        key = _challenge_key(cid)
        raw = await self._cache.get(key)
        if raw is None:
            return _fail(ErrorKeys.AuthChallengeExpired, "登录验证已过期,请重新登录")
        challenge = LoginOtpChallenge.from_json(raw)
        if challenge.fail_times >= MAX_OTP_FAILS:
            await self._cache.delete(key)
            return _fail(ErrorKeys.AuthChallengeExpired, "登录验证已过期,请重新登录")

        otp_row = await self._otp_repo.get_first(
            SysUserOtp.user_id == challenge.user_id, SysUserOtp.enabled == True  # noqa: E712
        )
        last_step = otp_row.last_used_time_step if otp_row else None
        result, matched_step = otp_service.validate(code, challenge.setup_secret, last_step)
        if result != otp_service.OK:
            if result == otp_service.REUSED:
                await self._write_login_log(
                    challenge.account, None, False, "动态码已被使用,请使用当前最新码", "login", remote_addr
                )
                return _fail(ErrorKeys.AuthOtpReused, "动态码已被使用,请使用当前最新码")
            remaining = await self._cache.ttl(key)
            if remaining is None or remaining <= 0:
                await self._cache.delete(key)
                return _fail(ErrorKeys.AuthChallengeExpired, "登录验证已过期,请重新登录")
            challenge.fail_times += 1
            await self._cache.set(key, challenge.to_json(), remaining)
            await self._cache.increment(_otp_error_key(challenge.account), 1, ERROR_WINDOW)
            await self._write_login_log(challenge.account, None, False, "校验码验证失败", "login", remote_addr)
            return _fail(ErrorKeys.AuthOtpVerifyFailed, "校验码验证失败")

        secret_cipher = encrypt(challenge.setup_secret)
        legacy = otp_row
        if legacy is None:
            legacy = await self._otp_repo.get_first(SysUserOtp.user_id == challenge.user_id)
        if legacy is not None:
            legacy.secret_cipher = secret_cipher
            legacy.last_used_time_step = matched_step
            if not legacy.enabled:
                legacy.bind_time = datetime.now(UTC)
            legacy.enabled = True
            await self._otp_repo.update(legacy)
        else:
            await self._otp_repo.add(
                SysUserOtp(
                    user_id=challenge.user_id,
                    secret_cipher=secret_cipher,
                    last_used_time_step=matched_step,
                    enabled=True,
                    bind_time=datetime.now(UTC),
                )
            )

        user = await self._user_repo.get_by_id(challenge.user_id)
        if user is None or user.status != 0:
            await self._cache.delete(key)
            return _fail(ErrorKeys.AuthChallengeExpired, "登录验证已过期,请重新登录")
        tenant_error = await self._verify_tenant(user)
        if tenant_error is not None:
            await self._cache.delete(key)
            await self._write_login_log(user.account, user.tenant_id, False, tenant_error, "login", remote_addr)
            return _fail(tenant_error, tenant_error)

        token, refresh, expired = await self._issue_tokens(user, remote_addr)
        await self._cache.delete(key)
        return LoginResult(success=True, token=token, refresh_token=refresh, password_expired=expired)

    async def logout(self, authorization: str | None, remote_addr: str | None = None) -> None:
        token = _extract_bearer(authorization)
        if not token:
            return
        try:
            claims = jose_jwt.get_unverified_claims(token)
            exp = datetime.fromtimestamp(int(claims.get("exp", 0)), tz=UTC)
            remaining = int((exp - datetime.now(UTC)).total_seconds())
            account = claims.get("acct")
            tenant_raw = claims.get("tid")
            tenant_id = int(tenant_raw) if tenant_raw not in (None, "") else DbConst.DefaultTenantId
            await self._write_login_log(account, tenant_id, True, "登出", "logout", remote_addr)
            if remaining > 0:
                await self._cache.set(_blacklist_key(token), "1", remaining)
        except Exception:
            logger.warning("登出 token 解析失败", exc_info=True)

    async def _issue_tokens(self, user: SysUser, remote_addr: str | None) -> tuple[str, str, bool]:
        claims = _build_claims(user)
        token = create_access_token(claims)
        refresh = create_refresh_token(claims)
        await self._cache.delete(_error_key(user.account or ""))
        await self._cache.delete(_otp_error_key(user.account or ""))
        await self._cache.set(f"{CacheConst.KeyUserToken}{user.id}", str(user.token_version))
        await self._cache.set_hash(
            CacheConst.KeyUserOnline,
            str(user.id),
            json.dumps(
                {
                    "userId": user.id,
                    "account": user.account,
                    "realName": user.real_name,
                    "tenantId": user.tenant_id,
                },
                ensure_ascii=False,
            ),
            CacheConst.OnlineUserTtl,
        )
        await self._write_login_log(user.account, user.tenant_id, True, "登录成功", "login", remote_addr)
        expired = await self._user_service.is_password_expired(user.id)
        return token, refresh, expired

    async def _is_otp_required(self) -> bool:
        value = await self._config.get_value_by_code(SysConfigService.OTP_ENABLED)
        return (value or "").strip().lower() != "false"

    async def _verify_tenant(self, user: SysUser) -> str | None:
        tenant_id = user.tenant_id or DbConst.DefaultTenantId
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if tenant is None:
            return ErrorKeys.TenantNotFound
        if tenant.status != 0:
            return ErrorKeys.TenantDisabled
        if tenant.expiration_time is not None and tenant.expiration_time < datetime.now(UTC):
            return ErrorKeys.TenantExpired
        return None

    async def _write_login_log(
        self,
        account: str | None,
        tenant_id: int | None,
        success: bool,
        message: str,
        login_type: str,
        remote_addr: str | None,
    ) -> None:
        try:
            await self._login_log.log_async(
                account, tenant_id or DbConst.DefaultTenantId, success, message, login_type, remote_addr
            )
        except Exception:
            logger.warning("登录日志写入失败", exc_info=True)


def _fail(error_code: str, msg: str) -> LoginResult:
    return LoginResult(success=False, error=msg, error_code=error_code)


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return authorization.strip() or None


def _try_decrypt(cipher_text: str | None) -> str | None:
    if not cipher_text:
        return None
    try:
        return decrypt(cipher_text)
    except Exception:
        return None


def _build_claims(user: SysUser) -> dict[str, object]:
    return {
        "uid": user.id,
        "acct": user.account or "",
        "rn": user.real_name or "",
        "org": user.org_id,
        "tid": user.tenant_id or DbConst.DefaultTenantId,
        "tv": user.token_version,
        "rids": [],
        "is_super": user.account_type == 999,
    }


def _build_otpauth_uri(account: str, secret: str) -> str:
    from urllib.parse import quote

    issuer = get_settings().otp.issuer
    label = quote(f"{issuer}:{account}", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer, safe='')}&digits=6&period=30"


def _next_challenge_id() -> int:
    from src.core.snowflake import next_id

    return next_id(get_settings().yit.worker_id)
