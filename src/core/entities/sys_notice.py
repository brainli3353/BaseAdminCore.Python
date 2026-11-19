from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant, EntityTenantBaseData


class SysNotice(EntityTenantBaseData):
    __tablename__ = "sys_notice"

    title: Mapped[str] = mapped_column("Title", String(256), nullable=False, default="")
    content: Mapped[str] = mapped_column("Content", Text, nullable=False, default="")
    type: Mapped[int] = mapped_column("Type", Integer, nullable=False, default=1, server_default=text("1"))
    public_user_id: Mapped[int] = mapped_column(
        "PublicUserId", BigInteger, nullable=False, default=0, server_default=text("0")
    )
    public_user_name: Mapped[str | None] = mapped_column("PublicUserName", String(32), nullable=True)
    public_org_id: Mapped[int] = mapped_column(
        "PublicOrgId", BigInteger, nullable=False, default=0, server_default=text("0")
    )
    public_org_name: Mapped[str | None] = mapped_column("PublicOrgName", String(64), nullable=True)
    public_time: Mapped[datetime | None] = mapped_column("PublicTime", DateTime(timezone=True), nullable=True)
    cancel_time: Mapped[datetime | None] = mapped_column("CancelTime", DateTime(timezone=True), nullable=True)
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))


class SysNoticeUser(EntityTenant):
    __tablename__ = "sys_notice_user"

    notice_id: Mapped[int] = mapped_column("NoticeId", BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column("UserId", BigInteger, nullable=False)
    read_time: Mapped[datetime | None] = mapped_column("ReadTime", DateTime(timezone=True), nullable=True)
    read_status: Mapped[int] = mapped_column(
        "ReadStatus", Integer, nullable=False, default=0, server_default=text("0")
    )
