"""Redis 缓存实现（redis.asyncio）。"""

from __future__ import annotations

import redis.asyncio as aioredis


class RedisCacheService:
    def __init__(self, connection_string: str) -> None:
        self._client = aioredis.Redis.from_url(connection_string, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        return bool(await self._client.set(key, value, ex=ttl_seconds))

    async def set_if_not_exists(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        return bool(await self._client.set(key, value, ex=ttl_seconds, nx=True))

    async def delete(self, key: str) -> bool:
        return bool(await self._client.delete(key))

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def increment(self, key: str, amount: int = 1, ttl_seconds: int | None = None) -> int:
        async with self._client.pipeline() as pipe:
            pipe.incrby(key, amount)
            if ttl_seconds:
                pipe.expire(key, ttl_seconds)
            result = await pipe.execute()
        return int(result[0])

    async def get_hash_all(self, key: str) -> dict[str, str]:
        return await self._client.hgetall(key)

    async def set_hash(self, key: str, field: str, value: str, ttl_seconds: int | None = None) -> bool:
        async with self._client.pipeline() as pipe:
            pipe.hset(key, field, value)
            if ttl_seconds:
                pipe.expire(key, ttl_seconds)
            await pipe.execute()
        return True

    async def delete_hash(self, key: str, field: str) -> bool:
        return bool(await self._client.hdel(key, field))

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        return bool(await self._client.expire(key, ttl_seconds))

    async def ttl(self, key: str) -> int | None:
        value = await self._client.ttl(key)
        return None if value < 0 else int(value)

    async def scan_keys(self, pattern: str) -> list[str]:
        keys: list[str] = []
        async for key in self._client.scan_iter(match=pattern):
            keys.append(key)
        return keys

    async def close(self) -> None:
        await self._client.aclose()
