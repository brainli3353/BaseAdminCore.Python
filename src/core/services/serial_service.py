from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.repository import Repository
from src.core.entities.sys_tooling import SysSerial
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult


class SysSerialService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysSerial)

    async def page(self, input: PageInput) -> PageResult[SysSerial]:
        conditions = []
        if input.keyword:
            conditions.append(SysSerial.type.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysSerial.order_no)

    async def detail(self, serial_id: int) -> SysSerial | None:
        return await self._repo.get_by_id(serial_id)

    async def add(self, data: dict) -> SysSerial:
        if await self._repo.get_first(SysSerial.type == data.get("type")):
            raise AppException("serial.type_duplicated", "流水号类型已存在")
        row = SysSerial(**data)
        await self._repo.add(row)
        return row

    async def update(self, serial_id: int, data: dict) -> SysSerial:
        row = await self._repo.get_by_id(serial_id)
        if row is None:
            raise AppException("serial.not_found", "流水号不存在")
        for field in ("seq", "expy", "reset_interval", "formater", "min", "max", "order_no", "status", "remark"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        return row

    async def delete(self, serial_id: int) -> None:
        row = await self._repo.get_by_id(serial_id)
        if row is None:
            raise AppException("serial.not_found", "流水号不存在")
        await self._repo.soft_delete(row)

    async def set_status(self, serial_id: int, status: int) -> None:
        row = await self._repo.get_by_id(serial_id)
        if row is None:
            raise AppException("serial.not_found", "流水号不存在")
        row.status = status
        await self._repo.update(row)

    async def next_seq_no(self, type_code: str, is_global: bool = False) -> str:
        row = await self._repo.get_first(SysSerial.type == type_code)
        if row is None:
            raise AppException("serial.not_found", "流水号类型不存在")
        if row.status != 0:
            raise AppException("serial.disabled", "流水号已停用")
        now = datetime.now(UTC)
        expy = _next_expy(now, row.reset_interval)
        if row.expy is None or row.expy <= now:
            row.seq = row.min
        row.seq += 1
        if row.seq > row.max:
            raise AppException("serial.exhausted", "流水号已用尽")
        row.expy = expy
        await self._repo.update(row)
        return _render(row.formater, row.seq, row.max)

    async def preview(self, type_code: str) -> str:
        row = await self._repo.get_first(SysSerial.type == type_code)
        if row is None:
            raise AppException("serial.not_found", "流水号类型不存在")
        return _render(row.formater, row.seq + 1, row.max)

    def get_type_list(self) -> list[str]:
        return []

    def get_slot_list(self) -> list[str]:
        return ["{SEQ}", "{yyyy}", "{yy}", "{MM}", "{dd}", "{HH}", "{mm}", "{ss}", "{TenantId}", "{UserId}", "{OrgId}"]


def _next_expy(now: datetime, interval: int) -> datetime:
    if interval == 1:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if interval == 2:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if interval == 3:
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(year=9999, month=12, day=31)


def _render(formater: str | None, seq: int, max_value: int) -> str:
    template = formater or "{SEQ}"
    digits = len(str(max_value))
    result = template.replace("{SEQ}", str(seq).zfill(digits))
    now = datetime.now()
    result = (
        result.replace("{yyyy}", f"{now.year:04d}")
        .replace("{yy}", f"{now.year % 100:02d}")
        .replace("{MM}", f"{now.month:02d}")
        .replace("{dd}", f"{now.day:02d}")
        .replace("{HH}", f"{now.hour:02d}")
        .replace("{mm}", f"{now.minute:02d}")
        .replace("{ss}", f"{now.second:02d}")
    )
    return result
