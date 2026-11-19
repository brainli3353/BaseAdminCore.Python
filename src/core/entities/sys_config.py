from __future__ import annotations

from sqlalchemy import Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysConfig(EntityTenant):
    __tablename__ = "sys_config"

    code: Mapped[str | None] = mapped_column("Code", String(64), nullable=True)
    value: Mapped[str | None] = mapped_column("Value", String(1024), nullable=True)
    group_code: Mapped[str | None] = mapped_column("GroupCode", String(64), nullable=True)
    sys_flag: Mapped[bool] = mapped_column(
        "SysFlag", Boolean, nullable=False, default=False, server_default=text("false")
    )
    remark: Mapped[str | None] = mapped_column("Remark", String(255), nullable=True)
    name: Mapped[str | None] = mapped_column("Name", String(255), nullable=True)
    enum_options: Mapped[str | None] = mapped_column("EnumOptions", String(1024), nullable=True)
