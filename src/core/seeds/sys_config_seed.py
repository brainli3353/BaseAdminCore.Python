from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.repository import Repository
from src.core.entities.sys_config import SysConfig
from src.core.seeds.runner import Seed, register


@register
class SysConfigSeed(Seed):
    order = 9

    async def run(self, session: AsyncSession) -> None:
        repo = Repository(session, SysConfig)
        rows = [
            (1300000000141, "记录操作日志", "sys_op_log", "True"),
            (1300000000142, "升级公告提示开关", "sys_upgrade", "True"),
            (1300000000143, "登录 OTP 第二道校验开关", "sys_otp_enabled", "True"),
            (1300000000144, "单点登录开关", "sys_single_login", "false"),
        ]
        for config_id, name, code, value in rows:
            if await repo.get_by_id(config_id) is not None:
                continue
            await repo.add(
                SysConfig(
                    id=config_id,
                    name=name,
                    code=code,
                    value=value,
                    group_code="Default",
                    sys_flag=True,
                )
            )
