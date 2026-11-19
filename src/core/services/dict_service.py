from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache.base import ICacheService
from src.core.constants import CacheConst, ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_dict import SysDictData, SysDictType
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult


class SysDictTypeService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysDictType)

    async def page(self, input: PageInput) -> PageResult[SysDictType]:
        conditions = []
        if input.keyword:
            conditions.append(SysDictType.name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysDictType.id.desc())

    async def add(self, data: dict) -> SysDictType:
        if await self._repo.get_first(SysDictType.code == data.get("code"), SysDictType.code.is_not(None)):
            raise AppException(ErrorKeys.DictTypeNotFound, "字典类型编码已存在")
        row = SysDictType(**data)
        await self._repo.add(row)
        return row

    async def update(self, type_id: int, data: dict) -> SysDictType:
        row = await self._repo.get_by_id(type_id)
        if row is None:
            raise AppException(ErrorKeys.DictTypeNotFound, "字典类型不存在")
        for field in ("name", "code", "is_enum", "is_enable", "remark"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        return row

    async def delete(self, type_id: int) -> None:
        row = await self._repo.get_by_id(type_id)
        if row is None:
            raise AppException(ErrorKeys.DictTypeNotFound, "字典类型不存在")
        await self._repo.soft_delete(row)
        await self._repo.session.execute(SysDictData.__table__.delete().where(SysDictData.dict_type_id == type_id))


class SysDictDataService:
    def __init__(self, session: AsyncSession, cache: ICacheService) -> None:
        self._repo = Repository(session, SysDictData)
        self._type_repo = Repository(session, SysDictType)
        self._cache = cache
        self._session = session

    async def page(self, input: PageInput, dict_type_id: int | None = None) -> PageResult[SysDictData]:
        conditions = []
        if dict_type_id is not None:
            conditions.append(SysDictData.dict_type_id == dict_type_id)
        if input.keyword:
            conditions.append(SysDictData.label.ilike(f"%{input.keyword}%"))
        return await self._repo.page(
            input.page_index,
            input.page_size,
            *conditions,
            order_by=[SysDictData.order_no, SysDictData.id.desc()],
        )

    async def add(self, data: dict) -> SysDictData:
        if await self._repo.get_first(
            SysDictData.dict_type_id == data.get("dict_type_id"),
            SysDictData.code == data.get("code"),
            SysDictData.code.is_not(None),
        ):
            raise AppException("dict.code_exists", "同类型下字典编码已存在")
        row = SysDictData(**data)
        await self._repo.add(row)
        await self._invalidate_type(data.get("dict_type_id"))
        return row

    async def update(self, data_id: int, data: dict) -> SysDictData:
        row = await self._repo.get_by_id(data_id)
        if row is None:
            raise AppException(ErrorKeys.DictDataNotFound, "字典值不存在")
        for field in (
            "code",
            "value",
            "label",
            "tag_type",
            "style_setting",
            "class_setting",
            "order_no",
            "is_enable",
            "ext_data",
            "remark",
        ):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        await self._invalidate_type(row.dict_type_id)
        return row

    async def set_status(self, data_id: int, is_enable: bool) -> None:
        row = await self._repo.get_by_id(data_id)
        if row is None:
            raise AppException(ErrorKeys.DictDataNotFound, "字典值不存在")
        row.is_enable = is_enable
        await self._repo.update(row)
        await self._invalidate_type(row.dict_type_id)

    async def delete(self, data_id: int) -> None:
        row = await self._repo.get_by_id(data_id)
        if row is None:
            raise AppException(ErrorKeys.DictDataNotFound, "字典值不存在")
        await self._repo.soft_delete(row)
        await self._invalidate_type(row.dict_type_id)

    async def list_by_code(self, code: str) -> list[dict]:
        cache_key = f"{CacheConst.KeyDict}{code}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return json.loads(cached)
        type_row = await self._type_repo.get_first(SysDictType.code == code)
        if type_row is None or not type_row.is_enable:
            return []
        rows = await self._repo.list(
            SysDictData.dict_type_id == type_row.id,
            SysDictData.is_enable == True,  # noqa: E712
            order_by=SysDictData.order_no,
        )
        result = [
            {
                "id": row.id,
                "code": row.code,
                "value": row.value,
                "label": row.label,
                "tagType": row.tag_type,
                "orderNo": row.order_no,
            }
            for row in rows
        ]
        await self._cache.set(cache_key, json.dumps(result, ensure_ascii=False), 7 * 24 * 3600)
        return result

    async def _invalidate_type(self, type_id: int | None) -> None:
        if type_id is None:
            return
        type_row = await self._type_repo.get_by_id(type_id)
        if type_row and type_row.code:
            await self._cache.delete(f"{CacheConst.KeyDict}{type_row.code}")
