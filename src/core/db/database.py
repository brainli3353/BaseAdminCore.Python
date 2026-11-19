"""数据库引擎/会话（单库优先，多库/租户切库后续批扩展）。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

_engines: dict[str, AsyncEngine] = {}
_session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}


def get_engine(config_id: str = "main") -> AsyncEngine:
    if config_id in _engines:
        return _engines[config_id]
    settings = get_settings()
    if config_id == "log":
        url = settings.log_connection_string()
    else:
        url = settings.main_connection_string()
    engine = create_async_engine(url, pool_size=20, max_overflow=10, pool_pre_ping=True, echo=False)
    _engines[config_id] = engine
    _session_factories[config_id] = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine


def get_session_factory(config_id: str = "main") -> async_sessionmaker[AsyncSession]:
    if config_id not in _session_factories:
        get_engine(config_id)
    return _session_factories[config_id]


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory("main")
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engines() -> None:
    for engine in _engines.values():
        await engine.dispose()
    _engines.clear()
    _session_factories.clear()


def all_models() -> list[type[Any]]:
    from src.core.db.base import Base

    return list(Base.__subclasses__())


def register_audit_events() -> None:
    from src.core.db import audit

    for model in _iter_concrete_models():
        event.listen(model, "before_insert", audit.on_before_insert)
        event.listen(model, "before_update", audit.on_before_update)


def _iter_concrete_models() -> list[type[Any]]:
    from src.core.db.base import Base

    result: list[type[Any]] = []
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if mapper.primary_key is not None:
            result.append(model)
    return result
