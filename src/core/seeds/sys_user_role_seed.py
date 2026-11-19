from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_user import SysUser, SysUserRole
from src.core.seeds.runner import Seed, register


@register
class SysUserRoleSeed(Seed):
    order = 6

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysUserRole)
        if await repo.get_by_id(40000) is not None:
            return
        admin = await session.execute(select(SysUser.id).where(SysUser.account == "admin"))
        admin_id = admin.scalar_one_or_none()
        if admin_id is None:
            return
        await repo.add(
            SysUserRole(id=40000, user_id=admin_id, role_id=20000, tenant_id=DbConst.DefaultTenantId)
        )
