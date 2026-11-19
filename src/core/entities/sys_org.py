from __future__ import annotations

from sqlalchemy import BigInteger, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysOrg(EntityTenant):
    __tablename__ = "sys_org"
    __table_args__ = (Index("i_sys_org_pid", "Pid"),)

    pid: Mapped[int] = mapped_column("Pid", BigInteger, nullable=False, default=0, server_default=text("0"))
    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    code: Mapped[str | None] = mapped_column("Code", String(64), nullable=True)
    sort: Mapped[int] = mapped_column("Sort", Integer, nullable=False, default=0, server_default=text("0"))
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
