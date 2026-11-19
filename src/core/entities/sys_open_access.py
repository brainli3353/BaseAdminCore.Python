from __future__ import annotations

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysOpenAccess(EntityTenant):
    __tablename__ = "sys_open_access"
    __table_args__ = (Index("i_sys_open_access_a", "AccessKey"),)

    access_key: Mapped[str] = mapped_column("AccessKey", String(128), nullable=False, default="")
    access_secret: Mapped[str] = mapped_column("AccessSecret", String(256), nullable=False, default="")
    bind_tenant_id: Mapped[int] = mapped_column(
        "BindTenantId", BigInteger, nullable=False, default=1
    )
    bind_user_id: Mapped[int] = mapped_column("BindUserId", BigInteger, nullable=False, default=0)
