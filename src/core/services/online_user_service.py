from __future__ import annotations

import json

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst
from src.core.db.context import UserContext


class SysOnlineUserService:
    def __init__(self, cache: ICacheService) -> None:
        self._cache = cache

    async def register(
        self, user_id: int, account: str | None, real_name: str | None, tenant_id: int | None
    ) -> None:
        payload = json.dumps(
            {"userId": user_id, "account": account, "realName": real_name, "tenantId": tenant_id},
            ensure_ascii=False,
        )
        await self._cache.set_hash(
            CacheConst.KeyUserOnline, str(user_id), payload, CacheConst.OnlineUserTtl
        )

    async def list(self, user: UserContext) -> list[dict]:
        rows = await self._cache.get_hash_all(CacheConst.KeyUserOnline)
        result = []
        for field, payload in rows.items():
            data = json.loads(payload)
            if not user.is_super_admin and data.get("tenantId") != user.tenant_id:
                continue
            data["connectionId"] = field
            result.append(data)
        return result

    async def force_offline(self, user_id: int) -> None:
        await self._cache.delete_hash(CacheConst.KeyUserOnline, str(user_id))
