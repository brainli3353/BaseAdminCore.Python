from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysLogMsg(EntityTenant):
    __tablename__ = "sys_log_msg"

    message_type: Mapped[str] = mapped_column("MessageType", String(64), nullable=False, default="")
    title: Mapped[str] = mapped_column("Title", String(64), nullable=False, default="")
    message: Mapped[str] = mapped_column("Message", Text, nullable=False, default="")
    receive_user_id: Mapped[int] = mapped_column("ReceiveUserId", BigInteger, nullable=False, default=0)
    receive_user_name: Mapped[str | None] = mapped_column("ReceiveUserName", String(32), nullable=True)
    receive_ip: Mapped[str | None] = mapped_column("ReceiveIp", String(256), nullable=True)
    receive_browser: Mapped[str | None] = mapped_column("ReceiveBrowser", String(128), nullable=True)
    receive_os: Mapped[str | None] = mapped_column("ReceiveOs", String(128), nullable=True)
    send_user_id: Mapped[int] = mapped_column("SendUserId", BigInteger, nullable=False, default=0)
    send_user_name: Mapped[str | None] = mapped_column("SendUserName", String(32), nullable=True)
    send_ip: Mapped[str | None] = mapped_column("SendIp", String(256), nullable=True)
    send_browser: Mapped[str | None] = mapped_column("SendBrowser", String(128), nullable=True)
    send_os: Mapped[str | None] = mapped_column("SendOs", String(128), nullable=True)
    send_time: Mapped[datetime] = mapped_column("SendTime", DateTime(timezone=True), nullable=False)
