from __future__ import annotations

from sqlalchemy import BigInteger, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysMenu(EntityTenant):
    __tablename__ = "sys_menu"
    __table_args__ = (Index("i_sys_menu_pid", "Pid"),)

    pid: Mapped[int] = mapped_column("Pid", BigInteger, nullable=False, default=0, server_default=text("0"))
    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    title: Mapped[str | None] = mapped_column("Title", String(64), nullable=True)
    type: Mapped[int] = mapped_column("Type", Integer, nullable=False, default=2, server_default=text("2"))
    permission: Mapped[str | None] = mapped_column("Permission", String(128), nullable=True)
    order_no: Mapped[int] = mapped_column("OrderNo", Integer, nullable=False, default=0, server_default=text("0"))
    icon: Mapped[str | None] = mapped_column("Icon", String(64), nullable=True)
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
    is_keep_alive: Mapped[int] = mapped_column(
        "IsKeepAlive", Integer, nullable=False, default=1, server_default=text("1")
    )
