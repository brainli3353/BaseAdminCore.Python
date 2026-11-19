from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.repository import Repository
from src.core.entities.sys_log import SysLogDiff, SysLogEx, SysLogHttp, SysLogOp
from src.core.entities.sys_log_login import SysLogLogin
from src.core.pagination import PageInput, PageResult


class SysLogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._op = Repository(session, SysLogOp)
        self._ex = Repository(session, SysLogEx)
        self._diff = Repository(session, SysLogDiff)
        self._http = Repository(session, SysLogHttp)
        self._login = Repository(session, SysLogLogin)

    async def page_login(
        self,
        input: PageInput,
        account: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> PageResult[SysLogLogin]:
        conditions = []
        if account:
            conditions.append(SysLogLogin.account == account)
        if start_time:
            conditions.append(SysLogLogin.create_time >= start_time)
        if end_time:
            conditions.append(SysLogLogin.create_time <= end_time)
        return await self._login.page(input.page_index, input.page_size, *conditions, order_by=SysLogLogin.id.desc())

    async def page_op(
        self,
        input: PageInput,
        account: str | None = None,
        controller: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> PageResult[SysLogOp]:
        conditions = []
        if account:
            conditions.append(SysLogOp.account == account)
        if controller:
            conditions.append(SysLogOp.controller_name.ilike(f"%{controller}%"))
        if start_time:
            conditions.append(SysLogOp.create_time >= start_time)
        if end_time:
            conditions.append(SysLogOp.create_time <= end_time)
        return await self._op.page(input.page_index, input.page_size, *conditions, order_by=SysLogOp.id.desc())

    async def detail_op(self, log_id: int) -> SysLogOp | None:
        return await self._op.get_by_id(log_id)

    async def page_ex(
        self,
        input: PageInput,
        account: str | None = None,
        remote_ip: str | None = None,
        controller: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> PageResult[SysLogEx]:
        conditions = []
        if account:
            conditions.append(SysLogEx.account == account)
        if remote_ip:
            conditions.append(SysLogEx.remote_ip == remote_ip)
        if controller:
            conditions.append(SysLogEx.controller_name.ilike(f"%{controller}%"))
        if start_time:
            conditions.append(SysLogEx.create_time >= start_time)
        if end_time:
            conditions.append(SysLogEx.create_time <= end_time)
        return await self._ex.page(input.page_index, input.page_size, *conditions, order_by=SysLogEx.id.desc())

    async def detail_ex(self, log_id: int) -> SysLogEx | None:
        return await self._ex.get_by_id(log_id)

    async def page_diff(
        self, input: PageInput, start_time: datetime | None = None, end_time: datetime | None = None
    ) -> PageResult[SysLogDiff]:
        conditions = []
        if start_time:
            conditions.append(SysLogDiff.create_time >= start_time)
        if end_time:
            conditions.append(SysLogDiff.create_time <= end_time)
        return await self._diff.page(input.page_index, input.page_size, *conditions, order_by=SysLogDiff.id.desc())

    async def detail_diff(self, log_id: int) -> SysLogDiff | None:
        return await self._diff.get_by_id(log_id)

    async def page_http(
        self,
        input: PageInput,
        account: str | None = None,
        url: str | None = None,
        http_method: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> PageResult[SysLogHttp]:
        conditions = []
        if account:
            conditions.append(SysLogHttp.account == account)
        if url:
            conditions.append(SysLogHttp.request_url.ilike(f"%{url}%"))
        if http_method:
            conditions.append(SysLogHttp.http_method == http_method)
        if status_code is not None:
            conditions.append(SysLogHttp.status_code == status_code)
        if start_time:
            conditions.append(SysLogHttp.create_time >= start_time)
        if end_time:
            conditions.append(SysLogHttp.create_time <= end_time)
        return await self._http.page(input.page_index, input.page_size, *conditions, order_by=SysLogHttp.id.desc())

    async def detail_http(self, log_id: int) -> SysLogHttp | None:
        return await self._http.get_by_id(log_id)

    async def write_op(self, **kwargs) -> None:
        await self._op.add(SysLogOp(**kwargs))

    async def write_ex(self, **kwargs) -> None:
        await self._ex.add(SysLogEx(**kwargs))
