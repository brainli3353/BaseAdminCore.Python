from __future__ import annotations

import hashlib
import hmac
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst, ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_open_access import SysOpenAccess
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult
from src.core.snowflake import next_id


class SysOpenAccessService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysOpenAccess)
        self._cache = cache
        self._session = session

    async def page(self, input: PageInput) -> PageResult[SysOpenAccess]:
        conditions = []
        if input.keyword:
            conditions.append(SysOpenAccess.access_key.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysOpenAccess.id.desc())

    async def add(self, bind_tenant_id: int, bind_user_id: int) -> tuple[SysOpenAccess, str]:
        secret = secrets.token_urlsafe(16)[:22]
        access_key = secrets.token_urlsafe(16)[:22]
        row = SysOpenAccess(
            id=next_id(),
            access_key=access_key,
            access_secret=secret,
            bind_tenant_id=bind_tenant_id,
            bind_user_id=bind_user_id,
        )
        await self._repo.add(row)
        return row, secret

    async def update(self, access_id: int, bind_tenant_id: int, bind_user_id: int) -> None:
        row = await self._repo.get_by_id(access_id)
        if row is None:
            raise AppException(ErrorKeys.OpenAccessNotFound, "身份不存在")
        row.bind_tenant_id = bind_tenant_id
        row.bind_user_id = bind_user_id
        await self._repo.update(row)
        await self._invalidate(row.access_key)

    async def delete(self, access_id: int) -> None:
        row = await self._repo.get_by_id(access_id)
        if row is None:
            raise AppException(ErrorKeys.OpenAccessNotFound, "身份不存在")
        await self._repo.soft_delete(row)
        await self._invalidate(row.access_key)

    async def reset_secret(self, access_id: int) -> str:
        row = await self._repo.get_by_id(access_id)
        if row is None:
            raise AppException(ErrorKeys.OpenAccessNotFound, "身份不存在")
        secret = secrets.token_urlsafe(16)[:22]
        row.access_secret = secret
        await self._repo.update(row)
        await self._invalidate(row.access_key)
        return secret

    async def generate_signature(self, access_key: str, timestamp: str, nonce: str) -> dict:
        row = await self._repo.get_first(SysOpenAccess.access_key == access_key)
        if row is None:
            raise AppException(ErrorKeys.OpenAccessNotFound, "身份不存在")
        sign = _sign(row.access_secret, access_key, timestamp, nonce)
        return {"accessKey": access_key, "timestamp": timestamp, "nonce": nonce, "sign": sign}

    async def get_identity(self, access_key: str) -> dict | None:
        key = f"{CacheConst.KeyOpenAccess}{access_key}"
        cached = await self._cache.get(key)
        if cached:
            import json

            return json.loads(cached)
        row = await self._repo.get_first(SysOpenAccess.access_key == access_key)
        if row is None:
            return None
        result = {
            "id": row.id,
            "accessKey": row.access_key,
            "accessSecret": row.access_secret,
            "bindTenantId": row.bind_tenant_id,
            "bindUserId": row.bind_user_id,
        }
        await self._cache.set(key, __import__("json").dumps(result), 7 * 24 * 3600)
        return result

    async def _invalidate(self, access_key: str) -> None:
        await self._cache.delete(f"{CacheConst.KeyOpenAccess}{access_key}")


def _sign(secret: str, access_key: str, timestamp: str, nonce: str) -> str:
    message = f"{access_key}\n{timestamp}\n{nonce}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
