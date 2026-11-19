from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.repository import Repository
from src.core.entities.sys_tooling import SysPrint
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult
from src.core.snowflake import next_id


class SysPrintService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysPrint)

    async def page(self, input: PageInput) -> PageResult[SysPrint]:
        conditions = []
        if input.keyword:
            conditions.append(SysPrint.name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysPrint.id.desc())

    async def detail(self, print_id: int) -> SysPrint | None:
        return await self._repo.get_by_id(print_id)

    async def add(self, data: dict) -> SysPrint:
        if await self._repo.get_first(SysPrint.name == data.get("name")):
            raise AppException("print.name_exists", "模板名称已存在")
        row = SysPrint(**data)
        await self._repo.add(row)
        return row

    async def update(self, print_id: int, data: dict) -> SysPrint:
        row = await self._repo.get_by_id(print_id)
        if row is None:
            raise AppException("print.not_found", "模板不存在")
        for field in ("name", "type", "status", "template", "remark"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        return row

    async def copy(self, print_id: int) -> SysPrint:
        source = await self._repo.get_by_id(print_id)
        if source is None:
            raise AppException("print.not_found", "模板不存在")
        clone = SysPrint(
            id=next_id(),
            name=f"{source.name} - copy",
            type=source.type,
            status=source.status,
            template=source.template,
            remark=source.remark,
        )
        await self._repo.add(clone)
        return clone

    async def delete(self, print_id: int) -> None:
        row = await self._repo.get_by_id(print_id)
        if row is None:
            raise AppException("print.not_found", "模板不存在")
        await self._repo.soft_delete(row)
