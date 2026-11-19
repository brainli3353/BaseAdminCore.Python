from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst, ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_tooling import SysRoleTable, SysTableFieldScope
from src.core.exceptions import AppException


class SysRoleTableService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysRoleTable)
        self._scope_repo = Repository(session, SysTableFieldScope)
        self._cache = cache
        self._session = session

    async def grant(self, role_id: int, items: list[str]) -> None:
        from src.core.entities.sys_role import SysRole

        if await self._session.get(SysRole, role_id) is None:
            raise AppException(ErrorKeys.RoleNotFound, "角色不存在")
        await self._session.execute(SysRoleTable.__table__.delete().where(SysRoleTable.role_id == role_id))
        for item in items:
            parts = item.split(":")
            if len(parts) != 2:
                continue
            await self._repo.add(SysRoleTable(role_id=role_id, table_name=parts[0], column_name=parts[1]))
        await self._cache.delete(f"{CacheConst.KeyRoleTable}{role_id}")
        await self._cache.delete(CacheConst.KeyRoleTableManaged)

    async def get_role_table(self, role_id: int) -> list[str]:
        rows = await self._repo.list(SysRoleTable.role_id == role_id)
        return [f"{r.table_name}:{r.column_name}" for r in rows]

    async def get_allowed_columns(self, role_ids: list[int]) -> dict[str, list[str]]:
        if not role_ids:
            return {}
        rows = await self._repo.list(SysRoleTable.role_id.in_(role_ids))
        result: dict[str, list[str]] = {}
        for row in rows:
            result.setdefault(row.table_name or "", []).append(row.column_name or "")
        return result

    async def get_managed_tables(self) -> list[str]:
        cached = await self._cache.get(CacheConst.KeyRoleTableManaged)
        if cached:
            return json.loads(cached)
        rows = await self._scope_repo.list(SysTableFieldScope.enabled == True)  # noqa: E712
        tables = sorted({r.table_name for r in rows if r.table_name})
        await self._cache.set(CacheConst.KeyRoleTableManaged, json.dumps(tables), 7 * 24 * 3600)
        return tables

    async def set_enabled(self, table_name: str, enabled: bool) -> None:
        rows = await self._scope_repo.list(SysTableFieldScope.table_name == table_name)
        for row in rows:
            await self._session.execute(
                SysTableFieldScope.__table__.delete().where(SysTableFieldScope.id == row.id)
            )
        if enabled:
            await self._scope_repo.add(SysTableFieldScope(table_name=table_name, enabled=True))
        await self._cache.delete(CacheConst.KeyRoleTableManaged)

    async def get_table_scopes(self) -> list[dict]:
        rows = await self._scope_repo.list()
        return [
            {"tableName": r.table_name, "enabled": r.enabled, "remark": r.remark, "roleCount": 0, "columnCount": 0}
            for r in rows
        ]
