from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysUser(EntityTenant):
    __tablename__ = "sys_user"
    __table_args__ = (
        Index("i_sys_user_account", "Account"),
        Index("i_sys_user_orgid", "OrgId"),
        Index("i_sys_user_status", "Status"),
    )

    account: Mapped[str | None] = mapped_column("Account", String(64), nullable=True)
    password: Mapped[str | None] = mapped_column("Password", String(256), nullable=True)
    real_name: Mapped[str | None] = mapped_column("RealName", String(64), nullable=True)
    status: Mapped[int] = mapped_column("Status", Integer, nullable=False, default=0, server_default=text("0"))
    account_type: Mapped[int] = mapped_column(
        "AccountType", Integer, nullable=False, default=777, server_default=text("777")
    )
    token_version: Mapped[int] = mapped_column(
        "TokenVersion", Integer, nullable=False, default=1, server_default=text("1")
    )
    org_id: Mapped[int | None] = mapped_column("OrgId", BigInteger, nullable=True)
    pos_id: Mapped[int | None] = mapped_column("PosId", BigInteger, nullable=True)
    last_change_password_time: Mapped[datetime | None] = mapped_column(
        "LastChangePasswordTime", DateTime(timezone=True), nullable=True
    )


class SysUserOtp(EntityTenant):
    __tablename__ = "sys_user_otp"

    user_id: Mapped[int] = mapped_column("UserId", BigInteger, nullable=False)
    secret_cipher: Mapped[str | None] = mapped_column("SecretCipher", String(256), nullable=True)
    last_used_time_step: Mapped[int | None] = mapped_column("LastUsedTimeStep", BigInteger, nullable=True)
    enabled: Mapped[bool] = mapped_column("Enabled", Boolean, nullable=False, default=True, server_default=text("true"))
    bind_time: Mapped[datetime | None] = mapped_column("BindTime", DateTime(timezone=True), nullable=True)


class SysUserPasswordRecord(EntityTenant):
    __tablename__ = "sys_user_password_record"

    user_id: Mapped[int] = mapped_column("UserId", BigInteger, nullable=False)
    password_hash: Mapped[str | None] = mapped_column("PasswordHash", String(256), nullable=True)


class SysUserRole(EntityTenant):
    __tablename__ = "sys_user_role"
    __table_args__ = (
        Index("i_sys_user_role_userid", "UserId"),
        Index("i_sys_user_role_roleid", "RoleId"),
    )

    user_id: Mapped[int] = mapped_column("UserId", BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column("RoleId", BigInteger, nullable=False)
