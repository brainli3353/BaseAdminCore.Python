from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_org import SysOrg
from src.core.seeds.runner import Seed, register


@register
class SysOrgSeed(Seed):
    order = 1

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysOrg)
        if await repo.get_by_id(50000) is not None:
            return
        await repo.add(
            SysOrg(
                id=50000,
                pid=0,
                name="总部",
                code="HQ",
                sort=0,
                remark="初始根机构(系统种子)",
                status=0,
                tenant_id=DbConst.DefaultTenantId,
            )
        )
