from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_org import SysOrg
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult


class SysOrgService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysOrg)

    async def page(self, input: PageInput) -> PageResult[SysOrg]:
        conditions = []
        if input.keyword:
            conditions.append(SysOrg.name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysOrg.sort)

    async def tree(self) -> list[dict]:
        rows = await self._repo.list(order_by=SysOrg.sort)
        nodes = {
            row.id: {
                "id": row.id,
                "pid": row.pid,
                "name": row.name,
                "code": row.code,
                "sort": row.sort,
                "status": row.status,
                "children": [],
            }
            for row in rows
        }
        roots: list[dict] = []
        for node in nodes.values():
            parent = nodes.get(node["pid"])
            if node["pid"] == 0 or parent is None:
                roots.append(node)
            else:
                parent["children"].append(node)
        return roots

    async def get_child_ids(self, org_id: int) -> set[int]:
        rows = await self._repo.list()
        children: dict[int, set[int]] = {}
        for row in rows:
            children.setdefault(row.pid, set()).add(row.id)
        result = {org_id}
        stack = [org_id]
        while stack:
            current = stack.pop()
            for child in children.get(current, set()):
                if child not in result:
                    result.add(child)
                    stack.append(child)
        return result

    async def add(self, data: dict) -> SysOrg:
        if await self._repo.get_first(SysOrg.code == data.get("code"), SysOrg.code.is_not(None)):
            raise AppException(ErrorKeys.OrgDuplicate, "机构编码已存在")
        org = SysOrg(**data)
        await self._repo.add(org)
        return org

    async def update(self, org_id: int, data: dict) -> SysOrg:
        org = await self._repo.get_by_id(org_id)
        if org is None:
            raise AppException(ErrorKeys.OrgNotFound, "机构不存在")
        for field in ("pid", "name", "code", "sort", "status", "remark"):
            if field in data and data[field] is not None:
                setattr(org, field, data[field])
        await self._repo.update(org)
        return org

    async def delete(self, org_id: int) -> None:
        org = await self._repo.get_by_id(org_id)
        if org is None:
            raise AppException(ErrorKeys.OrgNotFound, "机构不存在")
        if await self._repo.get_first(SysOrg.pid == org_id):
            raise AppException("org.has_children", "存在子机构,禁止删除")
        await self._repo.soft_delete(org)
