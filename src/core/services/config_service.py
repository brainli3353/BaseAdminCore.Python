"""系统配置读取（对齐上游 SysConfigService.GetConfigValueByCode）。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst
from src.core.db.repository import Repository
from src.core.entities.sys_config import SysConfig
from src.core.pagination import PageInput, PageResult


class SysConfigService:
    OTP_ENABLED = "sys_otp_enabled"
    SINGLE_LOGIN_ENABLED = "sys_single_login"
    OP_LOG = "sys_op_log"

    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysConfig)
        self._cache = cache

    async def page(self, input: PageInput) -> PageResult[SysConfig]:
        conditions = []
        if input.keyword:
            conditions.append(SysConfig.name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysConfig.id.desc())

    async def add(self, data: dict) -> SysConfig:
        row = SysConfig(**data)
        await self._repo.add(row)
        return row

    async def update(self, config_id: int, data: dict) -> SysConfig:
        row = await self._repo.get_by_id(config_id)
        if row is None:
            from src.core.exceptions import AppException

            raise AppException("config.not_found", "配置不存在")
        for field in ("code", "value", "group_code", "sys_flag", "remark", "name", "enum_options"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        if row.code:
            await self._cache.delete(f"{CacheConst.KeyConfig}{row.code}")
        return row

    async def delete(self, config_id: int) -> None:
        row = await self._repo.get_by_id(config_id)
        if row is None:
            from src.core.exceptions import AppException

            raise AppException("config.not_found", "配置不存在")
        await self._repo.soft_delete(row)
        if row.code:
            await self._cache.delete(f"{CacheConst.KeyConfig}{row.code}")

    async def get_value_by_code(self, code: str) -> str | None:
        key = f"{CacheConst.KeyConfig}{code}"
        cached = await self._cache.get(key)
        if cached is not None:
            return cached
        row = await self._repo.get_first(SysConfig.code == code)
        if row is None or row.value is None:
            return None
        await self._cache.set(key, row.value, 7 * 24 * 3600)
        return row.value

    async def get_bool(self, code: str, default: bool) -> bool:
        raw = await self.get_value_by_code(code)
        if raw is None:
            return default
        return raw.strip().lower() in ("true", "1")
