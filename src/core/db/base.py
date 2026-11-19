"""实体基类体系（对齐上游 EntityBaseId/EntityBase/EntityTenant/EntityBaseData*）。

 列名保持 PascalCase、主键列小写 id（与 .NET 上游库结构一致）；
 Python 属性用 snake_case，映射到显式列名。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EntityBaseId(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=False)


class EntityBase(EntityBaseId):
    """审计字段 + 软删标记。"""

    __abstract__ = True

    is_delete: Mapped[bool] = mapped_column(
        "IsDelete", Boolean, nullable=False, default=False, server_default=text("false")
    )
    delete_time: Mapped[datetime | None] = mapped_column("DeleteTime", DateTime(timezone=True), nullable=True)
    create_time: Mapped[datetime | None] = mapped_column("CreateTime", DateTime(timezone=True), nullable=True)
    create_user_id: Mapped[int | None] = mapped_column("CreateUserId", BigInteger, nullable=True)
    create_user_name: Mapped[str | None] = mapped_column("CreateUserName", String(64), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column("UpdateTime", DateTime(timezone=True), nullable=True)
    update_user_id: Mapped[int | None] = mapped_column("UpdateUserId", BigInteger, nullable=True)
    update_user_name: Mapped[str | None] = mapped_column("UpdateUserName", String(64), nullable=True)


class EntityTenant(EntityBase):
    """租户基座。"""

    __abstract__ = True

    tenant_id: Mapped[int | None] = mapped_column("TenantId", BigInteger, nullable=True)


class EntityBaseData(EntityBase):
    """机构数据权限基座。"""

    __abstract__ = True

    create_org_id: Mapped[int | None] = mapped_column("CreateOrgId", BigInteger, nullable=True)


class EntityBaseOrg(EntityBase):
    """无租户机构基座。"""

    __abstract__ = True

    create_org_id: Mapped[int | None] = mapped_column("CreateOrgId", BigInteger, nullable=True)


class EntityBaseUpdateData(EntityBaseData):
    """机构基座 + 更新机构。"""

    __abstract__ = True

    update_org_id: Mapped[int | None] = mapped_column("UpdateOrgId", BigInteger, nullable=True)


class EntityTenantBaseData(EntityTenant):
    """租户 + 机构数据权限基座。"""

    __abstract__ = True

    create_org_id: Mapped[int | None] = mapped_column("CreateOrgId", BigInteger, nullable=True)
