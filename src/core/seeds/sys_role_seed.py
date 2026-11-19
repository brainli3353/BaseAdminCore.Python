from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_role import SysRole
from src.core.seeds.runner import Seed, register


@register
class SysRoleSeed(Seed):
    order = 2

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysRole)
        if await repo.get_by_id(20000) is not None:
            return
        await repo.add(
            SysRole(
                id=20000,
                name="系统管理员",
                code="sys_admin",
                remark="内置角色:全部菜单权限,账号删除/权限变更受服务层保护",
                sys_flag=True,
                data_scope=1,
                tenant_id=DbConst.DefaultTenantId,
            )
        )
