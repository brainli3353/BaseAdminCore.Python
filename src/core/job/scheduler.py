from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.db.repository import Repository
from src.core.entities.sys_job import SysJobDetail, SysJobLog

logger = logging.getLogger("admincore.job")

JOBS: dict[str, Callable[[], Awaitable[None] | None]] = {}

INSTANCE_ID = "local"
NODE_TAG = ""


def register_job(name: str) -> Callable:
    def decorator(func: Callable[[], Awaitable[None] | None]) -> Callable:
        JOBS[name] = func
        return func

    return decorator


async def run_job_by_name(name: str) -> None:
    func = JOBS.get(name)
    if func is None:
        logger.warning("任务未注册: %s", name)
        return
    result = func()
    if inspect.isawaitable(result):
        await result


class JobScheduler:
    def __init__(self, session_factory: async_sessionmaker, poll_seconds: int = 5) -> None:
        self._session_factory = session_factory
        self._poll_seconds = poll_seconds
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        self._stopping.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stopping.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while not self._stopping.is_set():
            try:
                await self._tick()
            except Exception:
                logger.exception("任务调度轮次异常")
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=self._poll_seconds)
            except TimeoutError:
                continue

    async def _tick(self) -> None:
        async with self._session_factory() as session:
            repo = Repository(session, SysJobDetail)
            rows = await repo.list(SysJobDetail.enabled == True)  # noqa: E712
            now = datetime.now(UTC)
            for row in rows:
                if row.target_node and NODE_TAG and row.target_node.lower() != NODE_TAG.lower():
                    continue
                due = row.last_run_time is None or row.last_run_time + timedelta(seconds=row.interval) <= now
                if not due:
                    continue
                await self._execute(session, row.job_name, "scheduled")
                row.last_run_time = now
                await session.flush()

    async def _execute(self, session, job_name: str, trigger: str) -> None:
        started = datetime.now(UTC)
        success = True
        error = None
        try:
            await run_job_by_name(job_name)
        except Exception as exc:
            success = False
            error = str(exc)[:512]
            logger.exception("任务执行失败: %s", job_name)
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        await Repository(session, SysJobLog).add(
            SysJobLog(
                job_name=job_name,
                trigger=trigger,
                triggered_at=started,
                duration_ms=duration,
                success=success,
                error_msg=error,
                instance_id=INSTANCE_ID,
                node_tag=NODE_TAG or None,
            )
        )
        await session.commit()


@register_job("clean_sys_log")
async def clean_sys_log() -> None:
    from sqlalchemy import text

    from src.core.db.database import get_engine

    days = 30
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM sys_log_login WHERE \"CreateTime\" < now() - make_interval(days => :days)"),
            {"days": days},
        )
