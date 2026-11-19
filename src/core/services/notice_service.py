from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import DbConst, ErrorKeys
from src.core.db.context import UserContext
from src.core.db.repository import Repository
from src.core.entities.sys_message import SysLogMsg
from src.core.entities.sys_notice import SysNotice, SysNoticeUser
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult


class SysNoticeService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysNotice)
        self._user_repo = Repository(session, SysNoticeUser)
        self._session = session

    async def page(self, input: PageInput, user: UserContext) -> PageResult[SysNotice]:
        conditions = []
        if not user.is_super_admin:
            conditions.append(SysNotice.create_user_id == user.user_id)
        if input.keyword:
            conditions.append(SysNotice.title.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysNotice.id.desc())

    async def add(self, data: dict, user: UserContext) -> SysNotice:
        row = SysNotice(
            title=data.get("title") or "",
            content=data.get("content") or "",
            type=int(data.get("type") or 1),
            status=0,
            create_user_id=user.user_id,
            create_org_id=user.org_id,
            tenant_id=user.tenant_id,
        )
        await self._repo.add(row)
        return row

    async def update(self, notice_id: int, data: dict, user: UserContext) -> SysNotice:
        row = await self._owned(notice_id, user)
        if row.status == 1:
            raise AppException("notice.published_locked", "已发布通知不可修改")
        for field in ("title", "content", "type"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await self._repo.update(row)
        return row

    async def delete(self, notice_id: int, user: UserContext) -> None:
        row = await self._owned(notice_id, user)
        if row.status == 1:
            raise AppException("notice.published_locked", "已发布通知不可删除,请先撤回")
        await self._repo.soft_delete(row)
        await self._session.execute(
            text("DELETE FROM sys_notice_user WHERE \"NoticeId\" = :id"), {"id": notice_id}
        )

    async def public(self, notice_id: int, user_ids: list[int], user: UserContext) -> None:
        row = await self._owned(notice_id, user)
        now = datetime.now(UTC)
        row.status = 1
        row.public_time = now
        row.public_user_id = user.user_id or 0
        row.public_user_name = user.real_name
        row.public_org_id = user.org_id or 0
        await self._repo.update(row)
        await self._session.execute(text("DELETE FROM sys_notice_user WHERE \"NoticeId\" = :id"), {"id": notice_id})
        if not user_ids:
            user_ids = list(
                (
                    await self._session.execute(
                        text("SELECT id FROM sys_user WHERE \"IsDelete\" = false AND \"TenantId\" = :tid"),
                        {"tid": user.tenant_id or DbConst.DefaultTenantId},
                    )
                ).scalars().all()
            )
        for uid in user_ids:
            await self._user_repo.add(SysNoticeUser(notice_id=notice_id, user_id=uid, read_status=0))
        from src.core.realtime import publish_event

        await publish_event("public_notice", {"id": notice_id, "title": row.title})

    async def cancel(self, notice_id: int, user: UserContext) -> None:
        row = await self._owned(notice_id, user)
        row.status = 2
        row.cancel_time = datetime.now(UTC)
        await self._repo.update(row)

    async def set_read(self, notice_id: int, user: UserContext) -> None:
        row = await self._user_repo.get_first(
            SysNoticeUser.notice_id == notice_id, SysNoticeUser.user_id == user.user_id
        )
        if row is None:
            raise AppException(ErrorKeys.NoticeNotFound, "通知不存在")
        row.read_status = 1
        row.read_time = datetime.now(UTC)
        await self._user_repo.update(row)

    async def page_received(self, input: PageInput, user: UserContext) -> PageResult[SysNoticeUser]:
        return await self._user_repo.page(
            input.page_index,
            input.page_size,
            SysNoticeUser.user_id == user.user_id,
            order_by=SysNoticeUser.id.desc(),
        )

    async def unread_list(self, user: UserContext) -> list[SysNotice]:
        rows = await self._user_repo.list(
            SysNoticeUser.user_id == user.user_id, SysNoticeUser.read_status == 0
        )
        ids = [r.notice_id for r in rows]
        if not ids:
            return []
        return list(await self._repo.list(SysNotice.id.in_(ids)))

    async def last(self, user: UserContext) -> SysNotice | None:
        return await self._repo.get_first(
            SysNotice.status == 1, order_by=None
        )

    async def detail(self, notice_id: int, user: UserContext) -> SysNotice | None:
        return await self._repo.get_by_id(notice_id)

    async def _owned(self, notice_id: int, user: UserContext) -> SysNotice:
        row = await self._repo.get_by_id(notice_id)
        if row is None:
            raise AppException(ErrorKeys.NoticeNotFound, "通知不存在")
        if not user.is_super_admin and row.create_user_id != user.user_id:
            raise AppException(ErrorKeys.CommonForbidden, "仅发布人可操作")
        return row


class SysMessageService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysLogMsg)

    async def send_user(
        self, receive_user_id: int, title: str, message: str, message_type: str, user: UserContext
    ) -> None:
        if not title and not message:
            raise AppException("message.content_required", "消息内容必填")
        await self._repo.add(
            SysLogMsg(
                message_type=message_type,
                title=title or "",
                message=message or "",
                receive_user_id=receive_user_id,
                send_user_id=user.user_id or 0,
                send_user_name=user.real_name,
                send_time=datetime.now(UTC),
                tenant_id=user.tenant_id,
            )
        )
        from src.core.realtime import publish_event

        await publish_event(
            "receive_message",
            {"title": title, "message": message, "receiveUserId": receive_user_id},
        )

    async def send_all(self, title: str, message: str, message_type: str, user: UserContext) -> None:
        if not title and not message:
            raise AppException("message.content_required", "消息内容必填")
