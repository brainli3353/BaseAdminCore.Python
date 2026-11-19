from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_pos import SysPos
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult


class SysPosService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysPos)

    async def page(self, input: PageInput, status: int | None = None) -> PageResult[SysPos]:
        conditions = []
        if input.keyword:
            conditions.append(SysPos.name.ilike(f"%{input.keyword}%"))
        if status is not None:
            conditions.append(SysPos.status == status)
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysPos.sort)

    async def add(self, data: dict) -> SysPos:
        if await self._repo.get_first(SysPos.code == data.get("code"), SysPos.code.is_not(None)):
            raise AppException(ErrorKeys.PosCodeExists, "职位编码已存在")
        pos = SysPos(**data)
        await self._repo.add(pos)
        return pos

    async def update(self, pos_id: int, data: dict) -> SysPos:
        pos = await self._repo.get_by_id(pos_id)
        if pos is None:
            raise AppException(ErrorKeys.PosNotFound, "职位不存在")
        for field in ("name", "code", "sort", "status", "remark"):
            if field in data and data[field] is not None:
                setattr(pos, field, data[field])
        await self._repo.update(pos)
        return pos

    async def delete(self, pos_id: int) -> None:
        pos = await self._repo.get_by_id(pos_id)
        if pos is None:
            raise AppException(ErrorKeys.PosNotFound, "职位不存在")
        await self._repo.soft_delete(pos)
