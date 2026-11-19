from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityBase


class SysTenant(EntityBase):
    __tablename__ = "sys_tenant"

    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    plan: Mapped[str | None] = mapped_column("Plan", String(64), nullable=True)
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
    expiration_time: Mapped[datetime | None] = mapped_column("ExpirationTime", DateTime(timezone=True), nullable=True)
    order_no: Mapped[int] = mapped_column("OrderNo", Integer, nullable=False, default=100, server_default=text("100"))
    remark: Mapped[str | None] = mapped_column("Remark", String(128), nullable=True)
    connection: Mapped[str | None] = mapped_column("Connection", String(512), nullable=True)
    db_name: Mapped[str | None] = mapped_column("DbName", String(64), nullable=True)
