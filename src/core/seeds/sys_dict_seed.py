from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_dict import SysDictData, SysDictType
from src.core.seeds.runner import Seed, register


@register
class SysDictTypeSeed(Seed):
    order = 5

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysDictType)
        if await repo.get_by_id(50000) is not None:
            return
        await repo.add(
            SysDictType(
                id=50000,
                name="账号状态",
                code="account_status",
                is_enum=True,
                is_enable=True,
                remark="intel 账号状态机字典(0 待验号 1 观察 2 养号中 3 停用 4 冻结)",
                tenant_id=DbConst.DefaultTenantId,
            )
        )


@register
class SysDictDataSeed(Seed):
    order = 6

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysDictData)
        if await repo.get_by_id(60000) is not None:
            return
        values = [
            (60000, "0", "待验号", 5, 0),
            (60001, "1", "观察", 3, 1),
            (60002, "2", "养号中", 1, 2),
            (60003, "3", "停用", 5, 3),
            (60004, "4", "冻结", 4, 4),
        ]
        for data_id, code, label, tag_type, order in values:
            await repo.add(
                SysDictData(
                    id=data_id,
                    dict_type_id=50000,
                    code=code,
                    value=code,
                    label=label,
                    tag_type=tag_type,
                    order_no=order,
                    is_enum=True,
                    is_enable=True,
                    tenant_id=DbConst.DefaultTenantId,
                )
            )
