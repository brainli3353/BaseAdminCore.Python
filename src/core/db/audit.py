"""审计字段自动填充（SQLAlchemy 事件）+ 雪花主键。

 插入：id / CreateTime / CreateUserId / CreateUserName / TenantId / CreateOrgId / IsDelete 缺省。
 更新：UpdateTime / UpdateUserId / UpdateUserName / UpdateOrgId（如有）/ 软删 DeleteTime。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Mapper

from src.core.config import get_settings
from src.core.db.context import default_tenant_id, get_current_user
from src.core.snowflake import next_id


def _utcnow() -> datetime:
    return datetime.now(UTC)


def on_before_insert(mapper: Mapper, connection: object, target: object) -> None:
    now = _utcnow()
    worker_id = get_settings().yit.worker_id

    def set_if(attr: str, value: object, only_if_none: bool = True) -> None:
        current = getattr(target, attr, None)
        if current is None or not only_if_none:
            setattr(target, attr, value)

    if hasattr(target, "id") and target.id in (None, 0):
        target.id = next_id(worker_id)
    set_if("create_time", now)
    set_if("is_delete", False)

    user = get_current_user()
    if user:
        set_if("create_user_id", user.user_id)
        set_if("create_user_name", user.account)
    if hasattr(target, "tenant_id") and target.tenant_id is None:
        target.tenant_id = user.tenant_id if user else default_tenant_id()
    if user and user.org_id is not None and hasattr(target, "create_org_id"):
        if target.create_org_id is None:
            target.create_org_id = user.org_id


def on_before_update(mapper: Mapper, connection: object, target: object) -> None:
    target.update_time = _utcnow()
    user = get_current_user()
    if user:
        target.update_user_id = user.user_id
        target.update_user_name = user.account
        if hasattr(target, "update_org_id") and user.org_id is not None:
            target.update_org_id = user.org_id
    if getattr(target, "is_delete", False) and getattr(target, "delete_time", None) is None:
        target.delete_time = _utcnow()
