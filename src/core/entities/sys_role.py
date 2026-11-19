from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysRole(EntityTenant):
    __tablename__ = "sys_role"

    name: Mapped[str | None] = mapped_column("Name", String(64), nullable=True)
    code: Mapped[str | None] = mapped_column("Code", String(64), nullable=True)
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)
    sys_flag: Mapped[bool] = mapped_column(
        "SysFlag", Boolean, nullable=False, default=False, server_default=text("false")
    )
    data_scope: Mapped[int] = mapped_column(
        "DataScope", BigInteger, nullable=False, default=4, server_default=text("4")
    )


class SysRoleMenu(EntityTenant):
    __tablename__ = "sys_role_menu"
    __table_args__ = (
        Index("i_sys_role_menu_roleid", "RoleId"),
        Index("i_sys_role_menu_menuid", "MenuId"),
    )

    role_id: Mapped[int] = mapped_column("RoleId", BigInteger, nullable=False)
    menu_id: Mapped[int] = mapped_column("MenuId", BigInteger, nullable=False)


class SysRoleApi(EntityTenant):
    __tablename__ = "sys_role_api"

    role_id: Mapped[int] = mapped_column("RoleId", BigInteger, nullable=False)
    permission: Mapped[str | None] = mapped_column("Permission", String(128), nullable=True)


class SysRoleOrg(EntityTenant):
    __tablename__ = "sys_role_org"

    role_id: Mapped[int] = mapped_column("RoleId", BigInteger, nullable=False)
    org_id: Mapped[int] = mapped_column("OrgId", BigInteger, nullable=False)
