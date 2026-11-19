from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst, DbConst, ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_tenant import SysTenant
from src.core.entities.sys_user import SysUser
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult
from src.core.snowflake import next_id


class SysTenantService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysTenant)
        self._user_repo = Repository(session, SysUser)
        self._cache = cache
        self._session = session

    async def page(self, input: PageInput) -> PageResult[SysTenant]:
        conditions = []
        if input.keyword:
            conditions.append(SysTenant.name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(
            input.page_index, input.page_size, *conditions, order_by=[SysTenant.order_no, SysTenant.id.desc()]
        )

    async def add(self, data: dict) -> int:
        row = SysTenant(
            id=next_id(),
            name=data.get("name") or "",
            plan=data.get("plan"),
            status=0,
            expiration_time=data.get("expiration_time"),
            order_no=int(data.get("order_no") or 100),
            remark=data.get("remark"),
            connection=data.get("connection"),
            db_name=data.get("db_name"),
        )
        await self._repo.add(row)
        return row.id

    async def update(self, tenant_id: int, data: dict) -> None:
        row = await self._repo.get_by_id(tenant_id)
        if row is None:
            raise AppException(ErrorKeys.TenantNotFound, "租户不存在")
        if row.id == DbConst.DefaultTenantId:
            raise AppException("tenant.default_uneditable", "默认租户不可编辑")
        for field in ("name", "plan", "order_no", "remark", "connection", "db_name", "expiration_time"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)

    async def delete(self, tenant_id: int) -> None:
        row = await self._repo.get_by_id(tenant_id)
        if row is None:
            raise AppException(ErrorKeys.TenantNotFound, "租户不存在")
        if row.id == DbConst.DefaultTenantId:
            raise AppException("tenant.default_undeletable", "默认租户不可删除")
        await self._repo.soft_delete(row)
        await self._invalidate_users(tenant_id)

    async def set_status(self, tenant_id: int, status: int) -> None:
        row = await self._repo.get_by_id(tenant_id)
        if row is None:
            raise AppException(ErrorKeys.TenantNotFound, "租户不存在")
        if row.id == DbConst.DefaultTenantId:
            raise AppException("tenant.default_uneditable", "默认租户不可停用")
        row.status = status
        await self._repo.update(row)
        await self._invalidate_users(tenant_id)

    async def init_db(self, tenant_id: int) -> dict:
        row = await self._repo.get_by_id(tenant_id)
        if row is None:
            raise AppException(ErrorKeys.TenantNotFound, "租户不存在")
        if not row.connection:
            raise AppException("tenant.no_connection", "未配置独立库连接串")
        return {"tenantId": tenant_id, "tableCount": 0, "seedCount": 0, "database": row.db_name}

    async def _invalidate_users(self, tenant_id: int) -> None:
        user_ids = (
            await self._session.execute(text("SELECT id FROM sys_user WHERE \"TenantId\" = :tid"), {"tid": tenant_id})
        ).scalars().all()
        for uid in user_ids:
            await self._cache.delete(f"{CacheConst.KeyUserToken}{uid}")
