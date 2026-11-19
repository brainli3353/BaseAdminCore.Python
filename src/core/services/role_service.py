from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_role import SysRole, SysRoleApi, SysRoleMenu, SysRoleOrg
from src.core.entities.sys_user import SysUserRole
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult
from src.core.snowflake import next_id


class SysRoleService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysRole)
        self._menu_repo = Repository(session, SysRoleMenu)
        self._api_repo = Repository(session, SysRoleApi)
        self._org_repo = Repository(session, SysRoleOrg)
        self._user_role_repo = Repository(session, SysUserRole)
        self._cache = cache
        self._session = session

    async def page(self, input: PageInput) -> PageResult[SysRole]:
        conditions = []
        if input.keyword:
            conditions.append(SysRole.name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysRole.id.desc())

    async def add(self, data: dict) -> SysRole:
        if await self._repo.get_first(SysRole.code == data.get("code")):
            raise AppException(ErrorKeys.RoleCodeExists, "角色编码已存在")
        role = SysRole(**data)
        await self._repo.add(role)
        return role

    async def update(self, role_id: int, data: dict) -> SysRole:
        role = await self._repo.get_by_id(role_id)
        if role is None:
            raise AppException(ErrorKeys.RoleNotFound, "角色不存在")
        for field in ("name", "code", "remark", "data_scope"):
            if field in data and data[field] is not None:
                setattr(role, field, data[field])
        await self._repo.update(role)
        await self._invalidate_role(role_id)
        return role

    async def delete(self, role_id: int) -> None:
        role = await self._repo.get_by_id(role_id)
        if role is None:
            raise AppException(ErrorKeys.RoleNotFound, "角色不存在")
        if role.sys_flag:
            raise AppException(ErrorKeys.RoleBuiltInForbidden, "内置角色禁止删除")
        await self._repo.soft_delete(role)
        await self._session.execute(SysRoleMenu.__table__.delete().where(SysRoleMenu.role_id == role_id))
        await self._session.execute(SysRoleApi.__table__.delete().where(SysRoleApi.role_id == role_id))
        await self._session.execute(SysRoleOrg.__table__.delete().where(SysRoleOrg.role_id == role_id))
        await self._session.execute(SysUserRole.__table__.delete().where(SysUserRole.role_id == role_id))
        await self._invalidate_role(role_id)

    async def grant_menu(self, role_id: int, menu_ids: list[int]) -> None:
        await self._role_exists(role_id)
        await self._session.execute(SysRoleMenu.__table__.delete().where(SysRoleMenu.role_id == role_id))
        for menu_id in menu_ids:
            await self._menu_repo.add(SysRoleMenu(role_id=role_id, menu_id=menu_id))
        await self._invalidate_role(role_id)

    async def get_menu_ids(self, role_id: int) -> list[int]:
        rows = (
            await self._session.execute(select(SysRoleMenu.menu_id).where(SysRoleMenu.role_id == role_id))
        ).scalars().all()
        return sorted(rows)

    async def grant_api(self, role_id: int, permissions: list[str]) -> None:
        await self._role_exists(role_id)
        await self._session.execute(SysRoleApi.__table__.delete().where(SysRoleApi.role_id == role_id))
        for permission in permissions:
            await self._api_repo.add(SysRoleApi(role_id=role_id, permission=permission))
        await self._invalidate_role(role_id)

    async def get_api_list(self, role_id: int) -> list[str]:
        rows = (
            await self._session.execute(select(SysRoleApi.permission).where(SysRoleApi.role_id == role_id))
        ).scalars().all()
        return [p for p in rows if p]

    async def grant_org(self, role_id: int, org_ids: list[int]) -> None:
        await self._role_exists(role_id)
        await self._session.execute(SysRoleOrg.__table__.delete().where(SysRoleOrg.role_id == role_id))
        for org_id in org_ids:
            await self._org_repo.add(SysRoleOrg(role_id=role_id, org_id=org_id))
        await self._invalidate_role(role_id)

    async def get_org_list(self, role_id: int) -> list[int]:
        rows = (
            await self._session.execute(select(SysRoleOrg.org_id).where(SysRoleOrg.role_id == role_id))
        ).scalars().all()
        return sorted(rows)

    async def copy(self, role_id: int) -> SysRole:
        source = await self._repo.get_by_id(role_id)
        if source is None:
            raise AppException(ErrorKeys.RoleNotFound, "角色不存在")
        new_id = next_id()
        clone = SysRole(
            id=new_id,
            name=f"{source.name} - copy",
            code=f"{source.code}_copy" if source.code else None,
            remark=source.remark,
            sys_flag=False,
            data_scope=source.data_scope,
        )
        await self._repo.add(clone)
        for menu_id in await self.get_menu_ids(role_id):
            await self._menu_repo.add(SysRoleMenu(role_id=new_id, menu_id=menu_id))
        for permission in await self.get_api_list(role_id):
            await self._api_repo.add(SysRoleApi(role_id=new_id, permission=permission))
        for org_id in await self.get_org_list(role_id):
            await self._org_repo.add(SysRoleOrg(role_id=new_id, org_id=org_id))
        return clone

    async def _role_exists(self, role_id: int) -> None:
        if await self._repo.get_by_id(role_id) is None:
            raise AppException(ErrorKeys.RoleNotFound, "角色不存在")

    async def _invalidate_role(self, role_id: int) -> None:
        from src.core.services.menu_perm_service import MenuPermService

        await MenuPermService(self._session, self._cache).invalidate_role(role_id)
