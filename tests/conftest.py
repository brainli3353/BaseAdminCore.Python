from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.cache.cache_setup import get_cache_service
from src.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_admin_state():
    async def _run() -> None:
        engine = create_async_engine(get_settings().main_connection_string())
        try:
            async with engine.begin() as conn:
                await conn.execute(text("DELETE FROM sys_user_otp"))
                await conn.execute(text("DELETE FROM sys_log_login"))
        finally:
            await engine.dispose()
        cache = get_cache_service()
        await cache.delete("sys_password_error:admin")
        await cache.delete("sys_otp_error:admin")

    try:
        asyncio.run(_run())
    except Exception:
        pass
