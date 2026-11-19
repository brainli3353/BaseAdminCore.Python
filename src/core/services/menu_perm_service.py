from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst
from src.core.entities.sys_menu import SysMenu
from src.core.entities.sys_role import SysRoleApi, SysRoleMenu
from src.core.entities.sys_user import SysUserRole


class MenuPermService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._session = session
        self._cache = cache

    async def get_permissions(self, user_id: int) -> set[str]:
        key = f"{CacheConst.KeyUserApiPerm}{user_id}"
        cached = await self._cache.get(key)
        if cached is not None:
            return set(json.loads(cached))
        role_ids = (
            await self._session.execute(select(SysUserRole.role_id).where(SysUserRole.user_id == user_id))
        ).scalars().all()
        if not role_ids:
            return set()
        menu_ids = (
            await self._session.execute(select(SysRoleMenu.menu_id).where(SysRoleMenu.role_id.in_(role_ids)))
        ).scalars().all()
        permissions: set[str] = set()
        if menu_ids:
            rows = (
                await self._session.execute(
                    select(SysMenu.permission).where(SysMenu.id.in_(menu_ids), SysMenu.permission.is_not(None))
                )
            ).scalars().all()
            permissions = {p for p in rows if p}
        blacklist = (
            await self._session.execute(select(SysRoleApi.permission).where(SysRoleApi.role_id.in_(role_ids)))
        ).scalars().all()
        permissions -= {p for p in blacklist if p}
        await self._cache.set(key, json.dumps(sorted(permissions)), 7 * 24 * 3600)
        return permissions

    async def invalidate_user(self, user_id: int) -> None:
        await self._cache.delete(f"{CacheConst.KeyUserApiPerm}{user_id}")

    async def invalidate_role(self, role_id: int) -> None:
        user_ids = (
            await self._session.execute(select(SysUserRole.user_id).where(SysUserRole.role_id == role_id))
        ).scalars().all()
        for user_id in user_ids:
            await self.invalidate_user(user_id)
