from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.core.db.database import get_session
from src.core.pagination import PageInput
from src.core.responses import success
from src.core.services.menu_perm_service import MenuPermService
from src.core.services.menu_service import SysMenuService
from src.core.services.org_service import SysOrgService
from src.core.services.pos_service import SysPosService
from src.core.services.role_service import SysRoleService
from src.core.services.user_service import SysUserService
from src.web.deps import UserDep, get_cache_service

router = APIRouter(tags=["rbac"])


def _user_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysUserService:
    return SysUserService(session, get_cache_service())


def _role_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysRoleService:
    return SysRoleService(session, get_cache_service())


def _menu_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysMenuService:
    return SysMenuService(session)


def _org_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysOrgService:
    return SysOrgService(session)


def _pos_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysPosService:
    return SysPosService(session)


def _page(
    page_index: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: str | None = Query(None),
) -> PageInput:
    return PageInput(page_index=page_index, page_size=page_size, keyword=keyword)


def _dict(obj: Any, fields: tuple[str, ...]) -> dict:
    return {field: getattr(obj, field, None) for field in fields}


USER_FIELDS = ("id", "account", "real_name", "status", "account_type", "org_id", "pos_id", "create_time")
ROLE_FIELDS = ("id", "name", "code", "remark", "sys_flag", "data_scope", "create_time")
MENU_FIELDS = ("id", "pid", "name", "title", "type", "permission", "order_no", "icon", "status")
ORG_FIELDS = ("id", "pid", "name", "code", "sort", "status", "remark")
POS_FIELDS = ("id", "name", "code", "sort", "status", "remark")


@router.get("/sysUser/page")
async def user_page(
    user: UserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: Annotated[PageInput, Depends(_page)],
    status: int | None = Query(None),
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    result = await service.page(page, status=status)
    rows = [_dict(u, USER_FIELDS) for u in result.list]
    from src.core.services.column_scope_service import ColumnScopeService
    from src.core.services.role_table_service import SysRoleTableService

    rows = await ColumnScopeService(session, SysRoleTableService(session, get_cache_service())).prune(
        "sys_user", rows, user
    )
    return success({"total": result.total, "list": rows})


@router.post("/sysUser/add")
async def user_add(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    created = await service.add(body, body.get("role_ids") or [])
    return success(_dict(created, USER_FIELDS))


@router.post("/sysUser/update")
async def user_update(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    updated = await service.update(body["id"], body, body.get("role_ids"))
    return success(_dict(updated, USER_FIELDS))


@router.post("/sysUser/delete")
async def user_delete(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    await service.delete(int(body["id"]))
    return success()


@router.get("/sysUser/roleIds")
async def user_role_ids(
    user: UserDep,
    user_id: int = Query(...),
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    return success(await service.get_role_ids(user_id))


@router.post("/sysUser/grantRole")
async def user_grant_role(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    await service.grant_role(int(body["id"]), body.get("roleIds") or [])
    return success()


@router.post("/sysUser/updatePassword")
async def user_update_password(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    await service.update_password(user.user_id, body.get("oldPassword"), body.get("newPassword"))
    return success()


@router.post("/sysUser/resetPwd")
async def user_reset_pwd(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    await service.reset_pwd(int(body["id"]), body.get("password"))
    return success()


@router.post("/sysUser/unlockLogin")
async def user_unlock_login(
    body: dict,
    user: UserDep,
    service: SysUserService = Depends(_user_service),  # noqa: B008
):
    await service.unlock_login(body["account"])
    return success()


@router.get("/sysRole/page")
async def role_page(
    user: UserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: Annotated[PageInput, Depends(_page)],
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    result = await service.page(page)
    rows = [_dict(r, ROLE_FIELDS) for r in result.list]
    from src.core.services.column_scope_service import ColumnScopeService
    from src.core.services.role_table_service import SysRoleTableService

    rows = await ColumnScopeService(session, SysRoleTableService(session, get_cache_service())).prune(
        "sys_role", rows, user
    )
    return success({"total": result.total, "list": rows})


@router.post("/sysRole/add")
async def role_add(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    return success(_dict(await service.add(body), ROLE_FIELDS))


@router.post("/sysRole/update")
async def role_update(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    return success(_dict(await service.update(int(body["id"]), body), ROLE_FIELDS))


@router.post("/sysRole/delete")
async def role_delete(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    await service.delete(int(body["id"]))
    return success()


@router.post("/sysRole/grantMenu")
async def role_grant_menu(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    await service.grant_menu(int(body["id"]), body.get("menuIds") or [])
    return success()


@router.get("/sysRole/menu")
async def role_menu(
    user: UserDep,
    role_id: int = Query(...),
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    return success(await service.get_menu_ids(role_id))


@router.post("/sysRole/grantApi")
async def role_grant_api(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    await service.grant_api(int(body["id"]), body.get("permissions") or [])
    return success()


@router.get("/sysRole/api")
async def role_api(
    user: UserDep,
    role_id: int = Query(...),
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    return success(await service.get_api_list(role_id))


@router.post("/sysRole/grantOrg")
async def role_grant_org(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    await service.grant_org(int(body["id"]), body.get("orgIds") or [])
    return success()


@router.get("/sysRole/org")
async def role_org(
    user: UserDep,
    role_id: int = Query(...),
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    return success(await service.get_org_list(role_id))


@router.post("/sysRole/copy")
async def role_copy(
    body: dict,
    user: UserDep,
    service: SysRoleService = Depends(_role_service),  # noqa: B008
):
    return success(_dict(await service.copy(int(body["id"])), ROLE_FIELDS))


@router.get("/sysMenu/tree")
async def menu_tree(
    user: UserDep,
    service: SysMenuService = Depends(_menu_service),  # noqa: B008
):
    return success(await service.tree())


@router.get("/sysMenu/user")
async def menu_user(
    user: UserDep,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    service = SysMenuService(session)
    permissions = await MenuPermService(session, get_cache_service()).get_permissions(user.user_id or 0)
    return success(await service.login_menu_tree(user, permissions))


@router.post("/sysMenu/add")
async def menu_add(
    body: dict,
    user: UserDep,
    service: SysMenuService = Depends(_menu_service),  # noqa: B008
):
    return success(_dict(await service.add(body), MENU_FIELDS))


@router.post("/sysMenu/update")
async def menu_update(
    body: dict,
    user: UserDep,
    service: SysMenuService = Depends(_menu_service),  # noqa: B008
):
    return success(_dict(await service.update(int(body["id"]), body), MENU_FIELDS))


@router.post("/sysMenu/delete")
async def menu_delete(
    body: dict,
    user: UserDep,
    service: SysMenuService = Depends(_menu_service),  # noqa: B008
):
    await service.delete(int(body["id"]))
    return success()


@router.get("/sysOrg/page")
async def org_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysOrgService = Depends(_org_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(o, ORG_FIELDS) for o in result.list]})


@router.get("/sysOrg/tree")
async def org_tree(
    user: UserDep,
    service: SysOrgService = Depends(_org_service),  # noqa: B008
):
    return success(await service.tree())


@router.post("/sysOrg/add")
async def org_add(
    body: dict,
    user: UserDep,
    service: SysOrgService = Depends(_org_service),  # noqa: B008
):
    return success(_dict(await service.add(body), ORG_FIELDS))


@router.post("/sysOrg/update")
async def org_update(
    body: dict,
    user: UserDep,
    service: SysOrgService = Depends(_org_service),  # noqa: B008
):
    return success(_dict(await service.update(int(body["id"]), body), ORG_FIELDS))


@router.post("/sysOrg/delete")
async def org_delete(
    body: dict,
    user: UserDep,
    service: SysOrgService = Depends(_org_service),  # noqa: B008
):
    await service.delete(int(body["id"]))
    return success()


@router.get("/sysPos/page")
async def pos_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    status: int | None = Query(None),
    service: SysPosService = Depends(_pos_service),  # noqa: B008
):
    result = await service.page(page, status=status)
    return success({"total": result.total, "list": [_dict(p, POS_FIELDS) for p in result.list]})


@router.post("/sysPos/add")
async def pos_add(
    body: dict,
    user: UserDep,
    service: SysPosService = Depends(_pos_service),  # noqa: B008
):
    return success(_dict(await service.add(body), POS_FIELDS))


@router.post("/sysPos/update")
async def pos_update(
    body: dict,
    user: UserDep,
    service: SysPosService = Depends(_pos_service),  # noqa: B008
):
    return success(_dict(await service.update(int(body["id"]), body), POS_FIELDS))


@router.post("/sysPos/delete")
async def pos_delete(
    body: dict,
    user: UserDep,
    service: SysPosService = Depends(_pos_service),  # noqa: B008
):
    await service.delete(int(body["id"]))
    return success()
