from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst
from src.core.db.context import UserContext
from src.core.db.repository import Repository
from src.core.entities.sys_tooling import SysColumnCustom


class SysColumnCustomService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysColumnCustom)
        self._cache = cache

    async def get_detail(self, grid_id: str, user: UserContext) -> dict | None:
        key = f"{CacheConst.KeyColumnCustom}{user.user_id}:{grid_id}"
        cached = await self._cache.get(key)
        if cached:
            return json.loads(cached)
        row = await self._repo.get_first(
            SysColumnCustom.user_id == user.user_id, SysColumnCustom.grid_id == grid_id
        )
        if row is None:
            return None
        result = {
            "gridId": row.grid_id,
            "fixedData": _loads(row.fixed_data),
            "resizableData": _loads(row.resizable_data),
            "sortData": _loads(row.sort_data),
            "visibleData": _loads(row.visible_data),
        }
        await self._cache.set(key, json.dumps(result, ensure_ascii=False), 7 * 24 * 3600)
        return result

    async def store(self, grid_id: str, data: dict, user: UserContext) -> None:
        row = await self._repo.get_first(
            SysColumnCustom.user_id == user.user_id, SysColumnCustom.grid_id == grid_id
        )
        if row is None:
            row = SysColumnCustom(user_id=user.user_id, grid_id=grid_id)
            await self._repo.add(row)
        for field in ("fixedData", "resizableData", "sortData", "visibleData"):
            setattr(row, _column(field), json.dumps(data.get(field), ensure_ascii=False))
        await self._repo.update(row)
        await self._cache.delete(f"{CacheConst.KeyColumnCustom}{user.user_id}:{grid_id}")

    async def reset(self, grid_id: str, user: UserContext) -> None:
        row = await self._repo.get_first(
            SysColumnCustom.user_id == user.user_id, SysColumnCustom.grid_id == grid_id
        )
        if row is not None:
            await self._repo.session.execute(
                SysColumnCustom.__table__.delete().where(SysColumnCustom.id == row.id)
            )
        await self._cache.delete(f"{CacheConst.KeyColumnCustom}{user.user_id}:{grid_id}")


def _column(field: str) -> str:
    return {
        "fixedData": "fixed_data",
        "resizableData": "resizable_data",
        "sortData": "sort_data",
        "visibleData": "visible_data",
    }[field]


def _loads(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}
