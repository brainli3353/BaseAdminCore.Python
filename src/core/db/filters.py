"""全局查询过滤器（软删 / 租户 / 机构），在仓储层按模型自动应用。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, and_, false, or_
from sqlalchemy.sql import ColumnElement

from src.core.db.context import get_current_user


def apply_filters(
    stmt: Select,
    model: type[Any],
    *,
    include_deleted: bool = False,
    org_scope: tuple[str, object] | None = None,
) -> Select:
    conditions: list[ColumnElement[bool]] = []
    if hasattr(model, "is_delete") and not include_deleted:
        conditions.append(model.is_delete == False)  # noqa: E712
    if hasattr(model, "tenant_id"):
        user = get_current_user()
        if user is not None and not user.is_super_admin and user.tenant_id is not None:
            conditions.append(model.tenant_id == user.tenant_id)
    if org_scope and hasattr(model, "create_org_id"):
        kind, value = org_scope
        if kind == "self":
            conditions.append(model.create_user_id == value)
        elif kind == "orgs":
            if value:
                conditions.append(model.create_org_id.in_(value))
            else:
                conditions.append(false())
    if conditions:
        return stmt.where(*conditions)
    return stmt


def soft_delete_condition(model: type[Any]) -> ColumnElement[bool]:
    return model.is_delete == True  # noqa: E712


def org_scope_condition(model: type[Any], org_ids: set[int]) -> ColumnElement[bool]:
    if not org_ids:
        return false()
    condition = model.create_org_id.in_(org_ids)
    if hasattr(model, "update_org_id"):
        condition = or_(condition, model.update_org_id.in_(org_ids))
    return and_(condition, model.create_org_id.is_not(None))
