from __future__ import annotations

from sqlalchemy import Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysPos(EntityTenant):
    __tablename__ = "sys_pos"

    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    code: Mapped[str | None] = mapped_column("Code", String(64), nullable=True)
    sort: Mapped[int] = mapped_column("Sort", Integer, nullable=False, default=0, server_default=text("0"))
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
