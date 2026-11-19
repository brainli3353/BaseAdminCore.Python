from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.pagination import PageInput
from src.core.responses import success
from src.core.services.open_access_service import SysOpenAccessService
from src.core.services.tenant_service import SysTenantService
from src.web.deps import UserDep, get_cache_service

router = APIRouter(tags=["tenant-open"])


def _tenant_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysTenantService:
    return SysTenantService(session, get_cache_service())


def _open_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysOpenAccessService:
    return SysOpenAccessService(session, get_cache_service())


def _page(
    page_index: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: str | None = Query(None),
) -> PageInput:
    return PageInput(page_index=page_index, page_size=page_size, keyword=keyword)


TENANT_FIELDS = ("id", "name", "plan", "status", "expiration_time", "order_no", "remark", "db_name")
OPEN_FIELDS = ("id", "access_key", "bind_tenant_id", "bind_user_id", "create_time")


def _dict(obj, fields: tuple[str, ...]) -> dict:
    return {field: getattr(obj, field, None) for field in fields}


@router.get("/sysTenant/page")
async def tenant_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysTenantService = Depends(_tenant_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(r, TENANT_FIELDS) for r in result.list]})


@router.post("/sysTenant/add")
async def tenant_add(body: dict, user: UserDep, service: SysTenantService = Depends(_tenant_service)):  # noqa: B008
    return success(await service.add(body))


@router.post("/sysTenant/update")
async def tenant_update(body: dict, user: UserDep, service: SysTenantService = Depends(_tenant_service)):  # noqa: B008
    await service.update(int(body["id"]), body)
    return success()


@router.post("/sysTenant/delete")
async def tenant_delete(body: dict, user: UserDep, service: SysTenantService = Depends(_tenant_service)):  # noqa: B008
    await service.delete(int(body["id"]))
    return success()


@router.post("/sysTenant/setStatus")
async def tenant_set_status(body: dict, user: UserDep, service: SysTenantService = Depends(_tenant_service)):  # noqa: B008
    await service.set_status(int(body["id"]), int(body.get("status") or 0))
    return success()


@router.post("/sysTenant/initDb")
async def tenant_init_db(body: dict, user: UserDep, service: SysTenantService = Depends(_tenant_service)):  # noqa: B008
    return success(await service.init_db(int(body["id"])))


@router.get("/sysOpenAccess/page")
async def open_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysOpenAccessService = Depends(_open_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(r, OPEN_FIELDS) for r in result.list]})


@router.post("/sysOpenAccess/add")
async def open_add(body: dict, user: UserDep, service: SysOpenAccessService = Depends(_open_service)):  # noqa: B008
    row, secret = await service.add(int(body.get("bindTenantId") or 1), int(body.get("bindUserId") or 0))
    return success({"data": _dict(row, OPEN_FIELDS), "accessSecret": secret})


@router.post("/sysOpenAccess/update")
async def open_update(body: dict, user: UserDep, service: SysOpenAccessService = Depends(_open_service)):  # noqa: B008
    await service.update(int(body["id"]), int(body.get("bindTenantId") or 1), int(body.get("bindUserId") or 0))
    return success()


@router.post("/sysOpenAccess/delete")
async def open_delete(body: dict, user: UserDep, service: SysOpenAccessService = Depends(_open_service)):  # noqa: B008
    await service.delete(int(body["id"]))
    return success()


@router.post("/sysOpenAccess/resetSecret")
async def open_reset_secret(body: dict, user: UserDep, service: SysOpenAccessService = Depends(_open_service)):  # noqa: B008
    secret = await service.reset_secret(int(body["id"]))
    return success(secret)


@router.post("/sysOpenAccess/generateSignature")
async def open_generate_signature(body: dict, user: UserDep, service: SysOpenAccessService = Depends(_open_service)):  # noqa: B008
    return success(
        await service.generate_signature(
            body.get("accessKey") or "", body.get("timestamp") or "", body.get("nonce") or ""
        )
    )
