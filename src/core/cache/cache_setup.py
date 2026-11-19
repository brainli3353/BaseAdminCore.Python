"""缓存装配：Cache:Type=Redis 且连接串非空 → Redis，否则 Memory。"""

from __future__ import annotations

from src.core.cache.base import ICacheService
from src.core.cache.memory import MemoryCacheService
from src.core.cache.redis_impl import RedisCacheService
from src.core.config import get_settings

_cache: ICacheService | None = None


def get_cache_service() -> ICacheService:
    global _cache
    if _cache is None:
        settings = get_settings()
        if settings.cache.type == "Redis" and settings.redis_connectionstring:
            _cache = RedisCacheService(settings.redis_connectionstring)
        else:
            _cache = MemoryCacheService()
    return _cache


async def close_cache_service() -> None:
    global _cache
    if _cache is not None:
        await _cache.close()
        _cache = None
