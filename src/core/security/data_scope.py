from __future__ import annotations

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.context import UserContext


async def compute_data_scope(session: AsyncSession, user: UserContext) -> tuple[str, object] | None:
    if user is None or user.is_super_admin:
        return None
    rows = (
        await session.execute(
            text(
                'SELECT r."DataScope" AS scope, r."Id" AS role_id FROM sys_user_role ur '
                'JOIN sys_role r ON r."Id" = ur."RoleId" '
                'WHERE ur."UserId" = :uid AND r."IsDelete" = false'
            ),
            {"uid": user.user_id},
        )
    ).mappings().all()
    if not rows:
        return ("self", user.user_id)
    scopes = [int(r["scope"]) for r in rows]
    scope = min(scopes)
    if scope == 1:
        return None
    if scope == 4:
        return ("self", user.user_id)
    if scope == 3:
        return ("orgs", {user.org_id} if user.org_id is not None else set())
    if scope == 2:
        if user.org_id is None:
            return ("orgs", set())
        return ("orgs", await _child_org_ids(session, user.org_id))
    if scope == 5:
        role_ids = [int(r["role_id"]) for r in rows]
        org_ids = (
            await session.execute(
                text('SELECT "OrgId" FROM sys_role_org WHERE "RoleId" IN :rids').bindparams(
                    bindparam("rids", expanding=True)
                ),
                {"rids": role_ids},
            )
        ).scalars().all()
        return ("orgs", set(org_ids))
    return ("self", user.user_id)


async def _child_org_ids(session: AsyncSession, org_id: int) -> set[int]:
    rows = (await session.execute(text('SELECT "Id", "Pid" FROM sys_org WHERE "IsDelete" = false'))).mappings().all()
    children: dict[int, set[int]] = {}
    for row in rows:
        children.setdefault(int(row["Pid"]), set()).add(int(row["Id"]))
    result = {org_id}
    stack = [org_id]
    while stack:
        current = stack.pop()
        for child in children.get(current, set()):
            if child not in result:
                result.add(child)
                stack.append(child)
    return result
