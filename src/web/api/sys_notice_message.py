from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.pagination import PageInput
from src.core.responses import success
from src.core.services.notice_service import SysMessageService, SysNoticeService
from src.web.deps import UserDep

router = APIRouter(tags=["notice-message"])


def _notice_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysNoticeService:
    return SysNoticeService(session)


def _message_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysMessageService:
    return SysMessageService(session)


def _page(
    page_index: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: str | None = Query(None),
) -> PageInput:
    return PageInput(page_index=page_index, page_size=page_size, keyword=keyword)


NOTICE_FIELDS = (
    "id",
    "title",
    "content",
    "type",
    "status",
    "public_user_id",
    "public_user_name",
    "public_org_id",
    "public_org_name",
    "public_time",
    "cancel_time",
    "create_user_id",
    "create_time",
)


def _dict(obj, fields: tuple[str, ...]) -> dict:
    return {field: getattr(obj, field, None) for field in fields}


@router.get("/sysNotice/page")
async def notice_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysNoticeService = Depends(_notice_service),  # noqa: B008
):
    result = await service.page(page, user)
    return success({"total": result.total, "list": [_dict(r, NOTICE_FIELDS) for r in result.list]})


@router.post("/sysNotice/add")
async def notice_add(body: dict, user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    return success(_dict(await service.add(body, user), NOTICE_FIELDS))


@router.post("/sysNotice/update")
async def notice_update(body: dict, user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    return success(_dict(await service.update(int(body["id"]), body, user), NOTICE_FIELDS))


@router.post("/sysNotice/delete")
async def notice_delete(body: dict, user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    await service.delete(int(body["id"]), user)
    return success()


@router.post("/sysNotice/public")
async def notice_public(body: dict, user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    await service.public(int(body["id"]), body.get("userIds") or [], user)
    return success()


@router.post("/sysNotice/cancel")
async def notice_cancel(body: dict, user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    await service.cancel(int(body["id"]), user)
    return success()


@router.post("/sysNotice/setRead")
async def notice_set_read(body: dict, user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    await service.set_read(int(body["id"]), user)
    return success()


@router.get("/sysNotice/pageReceived")
async def notice_page_received(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysNoticeService = Depends(_notice_service),  # noqa: B008
):
    result = await service.page_received(page, user)
    fields = ("id", "notice_id", "read_status", "read_time")
    return success({"total": result.total, "list": [_dict(r, fields) for r in result.list]})


@router.get("/sysNotice/unReadList")
async def notice_unread_list(user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    rows = await service.unread_list(user)
    return success([_dict(r, NOTICE_FIELDS) for r in rows])


@router.get("/sysNotice/last")
async def notice_last(user: UserDep, service: SysNoticeService = Depends(_notice_service)):  # noqa: B008
    row = await service.last(user)
    return success(_dict(row, NOTICE_FIELDS) if row else None)


@router.get("/sysNotice/detail")
async def notice_detail(
    user: UserDep,
    id: int = Query(...),
    service: SysNoticeService = Depends(_notice_service),  # noqa: B008
):
    row = await service.detail(id, user)
    return success(_dict(row, NOTICE_FIELDS) if row else None)


@router.post("/sysMessage/sendUser")
async def message_send_user(body: dict, user: UserDep, service: SysMessageService = Depends(_message_service)):  # noqa: B008
    await service.send_user(
        int(body.get("receiveUserId") or 0),
        body.get("title") or "",
        body.get("message") or "",
        body.get("messageType") or "Info",
        user,
    )
    return success()


@router.post("/sysMessage/sendAll")
async def message_send_all(body: dict, user: UserDep, service: SysMessageService = Depends(_message_service)):  # noqa: B008
    await service.send_all(body.get("title") or "", body.get("message") or "", body.get("messageType") or "Info", user)
    return success()
