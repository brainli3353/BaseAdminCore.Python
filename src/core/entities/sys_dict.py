from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysDictType(EntityTenant):
    __tablename__ = "sys_dict_type"

    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    code: Mapped[str | None] = mapped_column("Code", String(64), nullable=True)
    is_enum: Mapped[bool] = mapped_column(
        "IsEnum", Boolean, nullable=False, default=False, server_default=text("false")
    )
    is_enable: Mapped[bool] = mapped_column(
        "IsEnable", Boolean, nullable=False, default=True, server_default=text("true")
    )
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)


class SysDictData(EntityTenant):
    __tablename__ = "sys_dict_data"

    dict_type_id: Mapped[int] = mapped_column("DictTypeId", Integer, nullable=False)
    code: Mapped[str | None] = mapped_column("Code", String(64), nullable=True)
    value: Mapped[str | None] = mapped_column("Value", String(128), nullable=True)
    label: Mapped[str | None] = mapped_column("Label", String(64), nullable=True)
    tag_type: Mapped[int] = mapped_column("TagType", Integer, nullable=False, default=1, server_default=text("1"))
    style_setting: Mapped[str | None] = mapped_column("StyleSetting", String(128), nullable=True)
    class_setting: Mapped[str | None] = mapped_column("ClassSetting", String(128), nullable=True)
    order_no: Mapped[int] = mapped_column("OrderNo", Integer, nullable=False, default=0, server_default=text("0"))
    is_enum: Mapped[bool] = mapped_column(
        "IsEnum", Boolean, nullable=False, default=False, server_default=text("false")
    )
    is_enable: Mapped[bool] = mapped_column(
        "IsEnable", Boolean, nullable=False, default=True, server_default=text("true")
    )
    ext_data: Mapped[str | None] = mapped_column("ExtData", String(512), nullable=True)
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)
