from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_pos import SysPos
from src.core.seeds.runner import Seed, register


@register
class SysPosSeed(Seed):
    order = 7

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysPos)
        if await repo.get_by_id(70000) is not None:
            return
        await repo.add(
            SysPos(
                id=70000,
                name="管理员",
                code="admin",
                sort=1,
                status=0,
                tenant_id=DbConst.DefaultTenantId,
            )
        )
