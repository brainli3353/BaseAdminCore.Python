from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst
from src.core.db.repository import Repository
from src.core.entities.sys_tenant import SysTenant
from src.core.entities.sys_user import SysUser
from src.core.services.auth.dto import UserTokenState


class UserTokenStateProvider:
    def __init__(self, session: AsyncSession) -> None:
        self._user_repo = Repository(session, SysUser)
        self._tenant_repo = Repository(session, SysTenant)

    async def get_user_state(self, user_id: int) -> UserTokenState | None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            return None
        tenant_id = user.tenant_id or DbConst.DefaultTenantId
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        tenant_valid = tenant is not None and tenant.status == 0 and (
            tenant.expiration_time is None or tenant.expiration_time >= datetime.now(UTC)
        )
        return UserTokenState(
            token_version=user.token_version,
            is_disabled=user.status != 0,
            tenant_valid=tenant_valid,
        )
