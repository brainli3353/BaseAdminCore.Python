from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysLogLogin(EntityTenant):
    __tablename__ = "sys_log_login"

    account: Mapped[str | None] = mapped_column("Account", String(64), nullable=True)
    remote_addr: Mapped[str | None] = mapped_column("RemoteAddr", String(64), nullable=True)
    status: Mapped[bool] = mapped_column("Status", Boolean, nullable=False, default=False)
    message: Mapped[str | None] = mapped_column("Message", String(256), nullable=True)
    login_type: Mapped[str | None] = mapped_column("LoginType", String(16), nullable=True)
    browser: Mapped[str | None] = mapped_column("Browser", String(128), nullable=True)
    os: Mapped[str | None] = mapped_column("Os", String(64), nullable=True)
