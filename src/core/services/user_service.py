from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.config import get_settings
from src.core.constants import CacheConst, ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_user import SysUser, SysUserPasswordRecord, SysUserRole
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult
from src.core.security.pbkdf2 import hash_password, verify_password


class SysUserService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysUser)
        self._role_repo = Repository(session, SysUserRole)
        self._pwd_repo = Repository(session, SysUserPasswordRecord)
        self._cache = cache
        self._session = session

    async def get_by_account(self, account: str) -> SysUser | None:
        return await self._repo.get_first(SysUser.account == account)

    async def get_by_id(self, user_id: int) -> SysUser | None:
        return await self._repo.get_by_id(user_id)

    async def page(self, input: PageInput, status: int | None = None, org_id: int | None = None) -> PageResult[SysUser]:
        conditions = []
        if input.keyword:
            conditions.append(SysUser.account.ilike(f"%{input.keyword}%"))
        if status is not None:
            conditions.append(SysUser.status == status)
        if org_id is not None:
            conditions.append(SysUser.org_id == org_id)
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysUser.id.desc())

    async def add(self, data: dict, role_ids: list[int]) -> SysUser:
        account = (data.get("account") or "").strip()
        if not account:
            raise AppException(ErrorKeys.CommonParamInvalid, "账号必填")
        if await self.get_by_account(account):
            raise AppException(ErrorKeys.UserAccountExists, "账号已存在")
        password = data.get("password")
        if not password:
            raise AppException(ErrorKeys.CommonParamInvalid, "密码必填")
        user = SysUser(
            account=account,
            password=hash_password(password),
            real_name=data.get("real_name"),
            status=data.get("status", 0),
            account_type=data.get("account_type", 777),
            org_id=data.get("org_id"),
            pos_id=data.get("pos_id"),
        )
        await self._repo.add(user)
        await self._replace_roles(user.id, role_ids)
        return user

    async def update(self, user_id: int, data: dict, role_ids: list[int] | None = None) -> SysUser:
        user = await self.get_by_id(user_id)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        for field in ("real_name", "status", "org_id", "pos_id", "account_type"):
            if field in data and data[field] is not None:
                setattr(user, field, data[field])
        if data.get("password"):
            user.password = hash_password(data["password"])
        await self._repo.update(user)
        if role_ids is not None:
            await self._replace_roles(user_id, role_ids)
        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        await self._repo.soft_delete(user)
        await self._role_repo.session.execute(
            SysUserRole.__table__.delete().where(SysUserRole.user_id == user_id)
        )
        await self._invalidate(user_id)

    async def get_role_ids(self, user_id: int) -> list[int]:
        rows = (
            await self._session.execute(select(SysUserRole.role_id).where(SysUserRole.user_id == user_id))
        ).scalars().all()
        return sorted(rows)

    async def grant_role(self, user_id: int, role_ids: list[int]) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        await self._replace_roles(user_id, role_ids)

    async def _replace_roles(self, user_id: int, role_ids: list[int]) -> None:
        await self._session.execute(SysUserRole.__table__.delete().where(SysUserRole.user_id == user_id))
        for role_id in role_ids:
            await self._role_repo.add(SysUserRole(user_id=user_id, role_id=role_id))
        await self._invalidate(user_id)

    async def update_password(self, user_id: int, old_password: str, new_password: str) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        if not verify_password(old_password, user.password):
            raise AppException(ErrorKeys.UserOldPasswordWrong, "原密码错误")
        self._check_strength(new_password)
        await self._add_password_record(user_id, user.password)
        user.password = hash_password(new_password)
        user.last_change_password_time = datetime.now(UTC)
        await self._bump_token_version(user)

    async def reset_pwd(self, user_id: int, new_password: str) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        self._check_strength(new_password)
        await self._add_password_record(user_id, user.password)
        user.password = hash_password(new_password)
        user.last_change_password_time = None
        await self._bump_token_version(user)

    async def unlock_login(self, account: str) -> None:
        user = await self.get_by_account(account)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        await self._cache.delete(f"{CacheConst.KeyPasswordError}{account}")
        await self._cache.delete(f"{CacheConst.KeyOtpError}{account}")

    async def offline(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise AppException(ErrorKeys.UserNotFound, "用户不存在")
        await self._bump_token_version(user)

    async def is_password_expired(self, user_id: int) -> bool:
        days = get_settings().sys_password.expiration_days
        if days <= 0:
            return False
        user = await self.get_by_id(user_id)
        if user is None or user.last_change_password_time is None:
            return True
        return user.last_change_password_time < datetime.now(UTC) - timedelta(days=days)

    async def _bump_token_version(self, user: SysUser) -> None:
        user.token_version += 1
        await self._repo.update(user)
        await self._cache.delete(f"{CacheConst.KeyUserToken}{user.id}")
        await self._invalidate(user.id)

    async def _add_password_record(self, user_id: int, password: str | None) -> None:
        if password:
            await self._pwd_repo.add(SysUserPasswordRecord(user_id=user_id, password_hash=password))

    def _check_strength(self, password: str) -> None:
        expression = get_settings().sys_password.strength_expression
        if not expression:
            if len(password) < 6:
                raise AppException(ErrorKeys.UserPasswordStrengthInvalid, "密码强度不足")
            return
        import re

        if not re.fullmatch(expression, password):
            raise AppException(ErrorKeys.UserPasswordStrengthInvalid, "密码强度不足")

    async def _invalidate(self, user_id: int) -> None:
        from src.core.services.menu_perm_service import MenuPermService

        await MenuPermService(self._session, self._cache).invalidate_user(user_id)
