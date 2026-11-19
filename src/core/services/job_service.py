from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.repository import Repository
from src.core.entities.sys_job import SysJobDetail, SysJobLog
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult


class SysJobService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysJobDetail)
        self._log_repo = Repository(session, SysJobLog)

    async def page(self, input: PageInput) -> PageResult[SysJobDetail]:
        conditions = []
        if input.keyword:
            conditions.append(SysJobDetail.job_name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysJobDetail.id.desc())

    async def add(self, data: dict) -> SysJobDetail:
        if await self._repo.get_first(SysJobDetail.job_name == data.get("job_name")):
            raise AppException("job.name_exists", "任务名已存在")
        row = SysJobDetail(**data)
        await self._repo.add(row)
        return row

    async def update(self, job_id: int, data: dict) -> SysJobDetail:
        row = await self._repo.get_by_id(job_id)
        if row is None:
            raise AppException("job.not_found", "任务不存在")
        for field in ("job_name", "interval", "enabled", "remark", "target_node"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        return row

    async def set_enabled(self, job_id: int, enabled: bool) -> None:
        row = await self._repo.get_by_id(job_id)
        if row is None:
            raise AppException("job.not_found", "任务不存在")
        row.enabled = enabled
        await self._repo.update(row)

    async def page_log(self, input: PageInput, job_name: str | None = None) -> PageResult[SysJobLog]:
        conditions = []
        if job_name:
            conditions.append(SysJobLog.job_name == job_name)
        return await self._log_repo.page(
            input.page_index, input.page_size, *conditions, order_by=SysJobLog.triggered_at.desc()
        )

    async def run_now(self, job_id: int) -> None:
        row = await self._repo.get_by_id(job_id)
        if row is None:
            raise AppException("job.not_found", "任务不存在")
        from src.core.job.scheduler import run_job_by_name

        await run_job_by_name(row.job_name)
