from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityBase, EntityTenant


class SysPrint(EntityTenant):
    __tablename__ = "sys_print"

    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    type: Mapped[int] = mapped_column("Type", Integer, nullable=False, default=1, server_default=text("1"))
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
    template: Mapped[str | None] = mapped_column("Template", Text, nullable=True)
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)


class SysColumnCustom(EntityTenant):
    __tablename__ = "sys_column_custom"
    __table_args__ = (UniqueConstraint("UserId", "GridId", name="u_sys_column_custom_user_grid"),)

    user_id: Mapped[int] = mapped_column("UserId", BigInteger, nullable=False)
    grid_id: Mapped[str | None] = mapped_column("GridId", String(128), nullable=True)
    fixed_data: Mapped[str | None] = mapped_column("FixedData", Text, nullable=True)
    resizable_data: Mapped[str | None] = mapped_column("ResizableData", Text, nullable=True)
    sort_data: Mapped[str | None] = mapped_column("SortData", Text, nullable=True)
    visible_data: Mapped[str | None] = mapped_column("VisibleData", Text, nullable=True)


class SysSerial(EntityTenant):
    __tablename__ = "sys_serial"

    seq: Mapped[int] = mapped_column("Seq", BigInteger, nullable=False, default=1, server_default=text("1"))
    expy: Mapped[datetime | None] = mapped_column("Expy", DateTime(timezone=True), nullable=True)
    type: Mapped[str | None] = mapped_column("Type", String(64), nullable=True)
    reset_interval: Mapped[int] = mapped_column(
        "ResetInterval", Integer, nullable=False, default=0, server_default=text("0")
    )
    formater: Mapped[str | None] = mapped_column("Formater", String(256), nullable=True)
    min: Mapped[int] = mapped_column("Min", BigInteger, nullable=False, default=1, server_default=text("1"))
    max: Mapped[int] = mapped_column("Max", BigInteger, nullable=False, default=1000000000, server_default=text("1000000000"))
    order_no: Mapped[int] = mapped_column("OrderNo", Integer, nullable=False, default=100, server_default=text("100"))
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)


class SysRoleTable(EntityBase):
    __tablename__ = "sys_role_table"
    __table_args__ = (UniqueConstraint("RoleId", "TableName", "ColumnName", name="u_sys_role_table"),)

    role_id: Mapped[int] = mapped_column("RoleId", BigInteger, nullable=False)
    table_name: Mapped[str | None] = mapped_column("TableName", String(128), nullable=True)
    column_name: Mapped[str | None] = mapped_column("ColumnName", String(128), nullable=True)


class SysTableFieldScope(EntityBase):
    __tablename__ = "sys_table_field_scope"

    table_name: Mapped[str | None] = mapped_column("TableName", String(128), nullable=True)
    enabled: Mapped[bool] = mapped_column(
        "Enabled", Boolean, nullable=False, default=True, server_default=text("true")
    )
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)
