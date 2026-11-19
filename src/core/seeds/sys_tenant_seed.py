from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_tenant import SysTenant
from src.core.seeds.runner import Seed, register


@register
class SysTenantSeed(Seed):
    order = 8

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysTenant)
        existing = await repo.get_by_id(DbConst.DefaultTenantId)
        if existing is not None:
            return
        await repo.add(
            SysTenant(
                id=DbConst.DefaultTenantId,
                name="默认租户",
                plan="标准版",
                status=0,
                order_no=1,
                remark="平台默认租户:存量数据天然归属,不可停用/删除",
            )
        )
