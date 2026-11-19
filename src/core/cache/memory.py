"""Memory 缓存实现（单进程；连接串为空时回退）。"""

from __future__ import annotations

import asyncio
import fnmatch
import time
from dataclasses import dataclass, field


@dataclass
class _Entry:
    value: str
    expire_at: float | None = None


@dataclass
class _Hash:
    fields: dict[str, str] = field(default_factory=dict)
    expire_at: float | None = None


class MemoryCacheService:
    def __init__(self) -> None:
        self._strings: dict[str, _Entry] = {}
        self._hashes: dict[str, _Hash] = {}
        self._lock = asyncio.Lock()

    def _expired(self, expire_at: float | None) -> bool:
        return expire_at is not None and expire_at <= time.time()

    async def get(self, key: str) -> str | None:
        async with self._lock:
            entry = self._strings.get(key)
            if entry is None:
                return None
            if self._expired(entry.expire_at):
                del self._strings[key]
                return None
            return entry.value

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        async with self._lock:
            self._strings[key] = _Entry(value, time.time() + ttl_seconds if ttl_seconds else None)
            return True

    async def set_if_not_exists(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        async with self._lock:
            entry = self._strings.get(key)
            if entry is not None and not self._expired(entry.expire_at):
                return False
            self._strings[key] = _Entry(value, time.time() + ttl_seconds if ttl_seconds else None)
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            existed = key in self._strings
            self._strings.pop(key, None)
            return existed

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def increment(self, key: str, amount: int = 1, ttl_seconds: int | None = None) -> int:
        async with self._lock:
            entry = self._strings.get(key)
            if entry is None or self._expired(entry.expire_at):
                new_value = amount
            else:
                try:
                    new_value = int(entry.value) + amount
                except ValueError:
                    new_value = amount
            self._strings[key] = _Entry(str(new_value), time.time() + ttl_seconds if ttl_seconds else None)
            return new_value

    async def get_hash_all(self, key: str) -> dict[str, str]:
        async with self._lock:
            h = self._hashes.get(key)
            if h is None or self._expired(h.expire_at):
                return {}
            return dict(h.fields)

    async def set_hash(self, key: str, field: str, value: str, ttl_seconds: int | None = None) -> bool:
        async with self._lock:
            h = self._hashes.setdefault(key, _Hash())
            h.fields[field] = value
            if ttl_seconds:
                h.expire_at = time.time() + ttl_seconds
            return True

    async def delete_hash(self, key: str, field: str) -> bool:
        async with self._lock:
            h = self._hashes.get(key)
            if h is None:
                return False
            return h.fields.pop(field, None) is not None

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        async with self._lock:
            entry = self._strings.get(key)
            if entry is None:
                return False
            entry.expire_at = time.time() + ttl_seconds
            return True

    async def ttl(self, key: str) -> int | None:
        async with self._lock:
            entry = self._strings.get(key)
            if entry is None or entry.expire_at is None:
                return None
            return max(0, int(entry.expire_at - time.time()))

    async def scan_keys(self, pattern: str) -> list[str]:
        async with self._lock:
            return [k for k in self._strings if fnmatch.fnmatch(k, pattern)]

    async def close(self) -> None:
        return None
