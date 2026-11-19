from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.pagination import PageInput
from src.core.responses import success
from src.core.services.config_service import SysConfigService
from src.core.services.dict_service import SysDictDataService, SysDictTypeService
from src.web.deps import UserDep, get_cache_service

router = APIRouter(tags=["dict-config"])


def _type_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysDictTypeService:
    return SysDictTypeService(session)


def _data_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysDictDataService:
    return SysDictDataService(session, get_cache_service())


def _config_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysConfigService:
    return SysConfigService(session, get_cache_service())


def _page(
    page_index: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: str | None = Query(None),
) -> PageInput:
    return PageInput(page_index=page_index, page_size=page_size, keyword=keyword)


def _dict(obj, fields: tuple[str, ...]) -> dict:
    return {field: getattr(obj, field, None) for field in fields}


TYPE_FIELDS = ("id", "name", "code", "is_enum", "is_enable", "remark")
DATA_FIELDS = (
    "id", "dict_type_id", "code", "value", "label", "tag_type", "style_setting",
    "class_setting", "order_no", "is_enum", "is_enable", "ext_data", "remark",
)
CONFIG_FIELDS = ("id", "code", "value", "group_code", "sys_flag", "remark", "name", "enum_options")


@router.get("/sysDictType/page")
async def type_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysDictTypeService = Depends(_type_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(r, TYPE_FIELDS) for r in result.list]})


@router.post("/sysDictType/add")
async def type_add(body: dict, user: UserDep, service: SysDictTypeService = Depends(_type_service)):  # noqa: B008
    return success(_dict(await service.add(body), TYPE_FIELDS))


@router.post("/sysDictType/update")
async def type_update(body: dict, user: UserDep, service: SysDictTypeService = Depends(_type_service)):  # noqa: B008
    return success(_dict(await service.update(int(body["id"]), body), TYPE_FIELDS))


@router.post("/sysDictType/delete")
async def type_delete(body: dict, user: UserDep, service: SysDictTypeService = Depends(_type_service)):  # noqa: B008
    await service.delete(int(body["id"]))
    return success()


@router.get("/sysDictData/page")
async def data_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    dict_type_id: int | None = Query(None),
    service: SysDictDataService = Depends(_data_service),  # noqa: B008
):
    result = await service.page(page, dict_type_id=dict_type_id)
    return success({"total": result.total, "list": [_dict(r, DATA_FIELDS) for r in result.list]})


@router.get("/sysDictData/list")
async def data_list(
    user: UserDep,
    code: str = Query(...),
    service: SysDictDataService = Depends(_data_service),  # noqa: B008
):
    return success(await service.list_by_code(code))


@router.post("/sysDictData/add")
async def data_add(body: dict, user: UserDep, service: SysDictDataService = Depends(_data_service)):  # noqa: B008
    return success(_dict(await service.add(body), DATA_FIELDS))


@router.post("/sysDictData/update")
async def data_update(body: dict, user: UserDep, service: SysDictDataService = Depends(_data_service)):  # noqa: B008
    return success(_dict(await service.update(int(body["id"]), body), DATA_FIELDS))


@router.post("/sysDictData/setStatus")
async def data_set_status(body: dict, user: UserDep, service: SysDictDataService = Depends(_data_service)):  # noqa: B008
    await service.set_status(int(body["id"]), bool(body.get("isEnable")))
    return success()


@router.post("/sysDictData/delete")
async def data_delete(body: dict, user: UserDep, service: SysDictDataService = Depends(_data_service)):  # noqa: B008
    await service.delete(int(body["id"]))
    return success()


@router.get("/sysConfig/page")
async def config_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysConfigService = Depends(_config_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(r, CONFIG_FIELDS) for r in result.list]})


@router.post("/sysConfig/add")
async def config_add(body: dict, user: UserDep, service: SysConfigService = Depends(_config_service)):  # noqa: B008
    return success(_dict(await service.add(body), CONFIG_FIELDS))


@router.post("/sysConfig/update")
async def config_update(body: dict, user: UserDep, service: SysConfigService = Depends(_config_service)):  # noqa: B008
    return success(_dict(await service.update(int(body["id"]), body), CONFIG_FIELDS))


@router.post("/sysConfig/delete")
async def config_delete(body: dict, user: UserDep, service: SysConfigService = Depends(_config_service)):  # noqa: B008
    await service.delete(int(body["id"]))
    return success()
