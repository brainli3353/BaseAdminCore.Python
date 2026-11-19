from __future__ import annotations

import logging
import uuid

from src.core.cache.cache_setup import get_cache_service
from src.core.constants import CacheConst
from src.core.db.base import Base
from src.core.db.database import get_engine, get_session_factory, register_audit_events
from src.core.seeds.runner import run_seeds

logger = logging.getLogger("admincore.schema")


async def create_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_schema() -> str:
    register_audit_events()
    cache = get_cache_service()
    instance_id = uuid.uuid4().hex
    lock_key = CacheConst.KeyStartupSchema
    if not await cache.set_if_not_exists(lock_key, instance_id, 120):
        held = await cache.get(lock_key)
        logger.warning("启动建表/种子被其他实例持有,跳过: holder=%s", held)
        return "SkippedHeldByOther"
    try:
        await create_tables()
        factory = get_session_factory()
        async with factory() as session:
            await run_seeds(session)
        return "Executed"
    finally:
        if await cache.get(lock_key) == instance_id:
            await cache.delete(lock_key)


async def ensure_worker_id(worker_id: int) -> bool:
    cache = get_cache_service()
    key = f"{CacheConst.KeyWorkerId}{worker_id}"
    if not await cache.set_if_not_exists(key, uuid.uuid4().hex, 300):
        logger.warning("雪花 WorkerId 已被其他实例占用: %s", worker_id)
        return False
    return True
