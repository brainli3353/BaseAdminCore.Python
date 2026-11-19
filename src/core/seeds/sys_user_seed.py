from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_user import SysUser
from src.core.security.pbkdf2 import hash_password
from src.core.seeds.runner import Seed, register
from src.core.snowflake import next_id


@register
class SysUserSeed(Seed):
    order = 5

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysUser)
        admin = await repo.get_first(SysUser.account == "admin")
        if admin is not None:
            changed = False
            if admin.account_type != 999:
                admin.account_type = 999
                changed = True
            if admin.tenant_id is None:
                admin.tenant_id = DbConst.DefaultTenantId
                changed = True
            if changed:
                await session.flush()
            return
        await repo.add(
            SysUser(
                id=next_id(),
                account="admin",
                password=hash_password("Admin@123"),
                real_name="系统管理员",
                account_type=999,
                status=0,
                tenant_id=DbConst.DefaultTenantId,
                org_id=50000,
            )
        )
