from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.context import UserContext

AUDIT_COLUMNS = {
    "id",
    "create_time",
    "create_user_id",
    "create_user_name",
    "update_time",
    "update_user_id",
    "update_user_name",
    "delete_time",
    "is_delete",
    "tenant_id",
    "create_org_id",
    "update_org_id",
}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class ColumnScopeService:
    def __init__(self, session: AsyncSession, role_table_service) -> None:
        self._session = session
        self._role_table = role_table_service

    async def prune(self, table_name: str, rows: list[dict], user: UserContext) -> list[dict]:
        if user.is_super_admin:
            return rows
        managed = await self._role_table.get_managed_tables()
        if table_name not in managed:
            return rows
        allowed = await self._role_table.get_allowed_columns(list(user.role_ids))
        columns = allowed.get(table_name)
        if columns is None:
            columns = []
        allowed_fields = {_snake(column) for column in columns} | AUDIT_COLUMNS
        result = []
        for row in rows:
            result.append({key: row.get(key) for key in row if key in allowed_fields})
        return result
