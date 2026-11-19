from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_menu import SysMenu
from src.core.exceptions import AppException


class SysMenuService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysMenu)

    async def tree(self) -> list[dict]:
        rows = await self._repo.list(order_by=SysMenu.order_no)
        return _build_tree(rows)

    async def login_menu_tree(self, user, permissions: set[str]) -> list[dict]:
        rows = await self._repo.list(order_by=SysMenu.order_no)
        if user.is_super_admin:
            rows = [r for r in rows if r.type != 3]
        else:
            rows = [r for r in rows if r.type != 3 or (r.permission and r.permission in permissions)]
        return _build_tree(rows)

    async def get_menu_ids(self, user_id: int, role_ids: tuple[int, ...]) -> set[int]:
        if not role_ids:
            return set()
        from sqlalchemy import select

        from src.core.entities.sys_role import SysRoleMenu

        rows = await self._session_execute(select(SysRoleMenu.menu_id).where(SysRoleMenu.role_id.in_(role_ids)))
        return set(rows.scalars().all())

    async def _session_execute(self, stmt):
        return await self._repo.session.execute(stmt)

    async def add(self, data: dict) -> SysMenu:
        if await self._repo.get_first(SysMenu.name == data["name"]):
            raise AppException(ErrorKeys.MenuNameExists, "菜单名称已存在")
        menu = SysMenu(**data)
        await self._repo.add(menu)
        return menu

    async def update(self, menu_id: int, data: dict) -> SysMenu:
        menu = await self._repo.get_by_id(menu_id)
        if menu is None:
            raise AppException(ErrorKeys.MenuNotFound, "菜单不存在")
        for key, value in data.items():
            if value is not None:
                setattr(menu, key, value)
        await self._repo.update(menu)
        return menu

    async def delete(self, menu_id: int) -> None:
        menu = await self._repo.get_by_id(menu_id)
        if menu is None:
            raise AppException(ErrorKeys.MenuNotFound, "菜单不存在")
        if await self._repo.get_first(SysMenu.pid == menu_id):
            raise AppException("menu.has_children", "存在子节点,禁止删除")
        await self._repo.soft_delete(menu)


def _build_tree(rows: list[SysMenu]) -> list[dict]:
    nodes = {
        row.id: {
            "id": row.id,
            "pid": row.pid,
            "name": row.name,
            "title": row.title,
            "type": row.type,
            "permission": row.permission,
            "orderNo": row.order_no,
            "icon": row.icon,
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
