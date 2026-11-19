"""登录日志写入（对齐上游 SysLogLoginService）。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.repository import Repository
from src.core.entities.sys_log_login import SysLogLogin


class SysLogLoginService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysLogLogin)

    async def log_async(
        self,
        account: str | None,
        tenant_id: int | None,
        success: bool,
        message: str,
        login_type: str,
        remote_addr: str | None = None,
    ) -> None:
        await self._repo.add(
            SysLogLogin(
                account=account,
                tenant_id=tenant_id,
                status=success,
                message=message,
                login_type=login_type,
                remote_addr=remote_addr,
            )
        )
        await self._repo.session.flush()
