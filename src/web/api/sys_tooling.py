from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.pagination import PageInput
from src.core.responses import success
from src.core.services.code_gen_service import CodeGenService
from src.core.services.column_custom_service import SysColumnCustomService
from src.core.services.database_service import SysDatabaseService
from src.core.services.export_service import export_xlsx
from src.core.services.import_service import parse_xlsx
from src.core.services.localization_service import LocalizationService
from src.core.services.pos_service import SysPosService
from src.core.services.print_service import SysPrintService
from src.core.services.role_table_service import SysRoleTableService
from src.core.services.serial_service import SysSerialService
from src.core.services.user_service import SysUserService
from src.web.deps import UserDep, get_cache_service

router = APIRouter(tags=["tooling"])


def _page(
    page_index: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: str | None = Query(None),
) -> PageInput:
    return PageInput(page_index=page_index, page_size=page_size, keyword=keyword)


def _dict(obj, fields: tuple[str, ...]) -> dict:
    return {field: getattr(obj, field, None) for field in fields}


@router.get("/sysPrint/page")
async def print_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    result = await SysPrintService(session).page(page)
    fields = ("id", "name", "type", "status", "remark", "create_time")
    return success({"total": result.total, "list": [_dict(r, fields) for r in result.list]})


@router.get("/sysPrint/detail")
async def print_detail(
    user: UserDep,
    id: int = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    row = await SysPrintService(session).detail(id)
    fields = ("id", "name", "type", "status", "template", "remark")
    return success(_dict(row, fields) if row else None)


@router.post("/sysPrint/add")
async def print_add(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    row = await SysPrintService(session).add(body)
    return success(_dict(row, ("id", "name", "type", "status", "remark")))


@router.post("/sysPrint/update")
async def print_update(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    row = await SysPrintService(session).update(int(body["id"]), body)
    return success(_dict(row, ("id", "name", "type", "status", "remark")))


@router.post("/sysPrint/copy")
async def print_copy(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    row = await SysPrintService(session).copy(int(body["id"]))
    return success(_dict(row, ("id", "name", "type", "status", "remark")))


@router.post("/sysPrint/delete")
async def print_delete(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysPrintService(session).delete(int(body["id"]))
    return success()


@router.get("/sysColumnCustom/get")
async def column_custom_get(
    user: UserDep,
    gridId: str = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    return success(await SysColumnCustomService(session, get_cache_service()).get_detail(gridId, user))


@router.post("/sysColumnCustom/store")
async def column_custom_store(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysColumnCustomService(session, get_cache_service()).store(body.get("gridId") or "", body, user)
    return success()


@router.post("/sysColumnCustom/reset")
async def column_custom_reset(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysColumnCustomService(session, get_cache_service()).reset(body.get("gridId") or "", user)
    return success()


@router.get("/sysSerial/page")
async def serial_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    result = await SysSerialService(session).page(page)
    fields = ("id", "type", "seq", "formater", "min", "max", "order_no", "status", "remark")
    return success({"total": result.total, "list": [_dict(r, fields) for r in result.list]})


@router.get("/sysSerial/detail")
async def serial_detail(
    user: UserDep,
    id: int = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    row = await SysSerialService(session).detail(id)
    fields = ("id", "type", "seq", "expy", "reset_interval", "formater", "min", "max", "order_no", "status", "remark")
    return success(_dict(row, fields) if row else None)


@router.post("/sysSerial/add")
async def serial_add(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    return success(_dict(await SysSerialService(session).add(body), ("id", "type", "status")))


@router.post("/sysSerial/update")
async def serial_update(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    row = await SysSerialService(session).update(int(body["id"]), body)
    return success(_dict(row, ("id", "type", "status")))


@router.post("/sysSerial/delete")
async def serial_delete(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysSerialService(session).delete(int(body["id"]))
    return success()


@router.post("/sysSerial/setStatus")
async def serial_set_status(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysSerialService(session).set_status(int(body["id"]), int(body.get("status") or 0))
    return success()


@router.get("/sysSerial/nextSeqNo")
async def serial_next(
    user: UserDep,
    type: str = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    return success(await SysSerialService(session).next_seq_no(type))


@router.get("/sysSerial/globalNextSeqNo")
async def serial_global_next(
    user: UserDep,
    type: str = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    return success(await SysSerialService(session).next_seq_no(type, is_global=True))


@router.get("/sysSerial/preview")
async def serial_preview(
    user: UserDep,
    type: str = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    return success(await SysSerialService(session).preview(type))


@router.get("/sysSerial/typeList")
async def serial_type_list(user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    rows = await SysSerialService(session).page(PageInput(page_index=1, page_size=200))
    return success([r.type for r in rows.list])


@router.get("/sysSerial/slotList")
async def serial_slot_list(user: UserDep):
    return success(
        ["{SEQ}", "{yyyy}", "{yy}", "{MM}", "{dd}", "{HH}", "{mm}", "{ss}", "{TenantId}", "{UserId}", "{OrgId}"]
    )


@router.post("/sysRole/grantTable")
async def role_table_grant(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysRoleTableService(session, get_cache_service()).grant(int(body["id"]), body.get("items") or [])
    return success()


@router.get("/sysRole/table")
async def role_table_get(
    user: UserDep,
    roleId: int = Query(...),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    return success(await SysRoleTableService(session, get_cache_service()).get_role_table(roleId))


@router.get("/sysRole/allTableColumn")
async def role_table_all(user: UserDep):
    return success([])


@router.get("/sysRole/tableScope")
async def role_table_scope(user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    return success(await SysRoleTableService(session, get_cache_service()).get_table_scopes())


@router.post("/sysRole/setTableScope")
async def role_table_set_scope(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    await SysRoleTableService(session, get_cache_service()).set_enabled(
        body.get("tableName") or "", bool(body.get("enabled"))
    )
    return success()


@router.get("/sysDatabase/tables")
async def db_tables(user: UserDep, keyword: str | None = Query(None)):
    return success(await SysDatabaseService().list_tables(keyword))


@router.get("/sysDatabase/columns")
async def db_columns(user: UserDep, table: str = Query(...)):
    return success(await SysDatabaseService().list_columns(table))


@router.get("/sysDatabase/indexes")
async def db_indexes(user: UserDep, table: str = Query(...)):
    return success(await SysDatabaseService().list_indexes(table))


@router.get("/sysCodeGen/tables")
async def codegen_tables(
    user: UserDep,
    keyword: str | None = Query(None),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    return success(await CodeGenService(session).get_table_list(keyword))


@router.post("/sysCodeGen/preview")
async def codegen_preview(body: dict, user: UserDep, session: AsyncSession = Depends(get_session)):  # noqa: B008
    return success(
        await CodeGenService(session).preview(
            body.get("tableName") or "",
            body.get("className"),
            body.get("moduleName") or "Business",
            body.get("removePrefix") if body.get("removePrefix") is not None else "sys_",
            body.get("baseType") or "EntityBase",
        )
    )


@router.get("/sysLocalization/cultures")
async def localization_cultures(user: UserDep):
    return success(LocalizationService().get_cultures())


@router.get("/sysLocalization/lang")
async def localization_lang(user: UserDep, culture: str = Query("zh-CN")):
    return success(LocalizationService().get_language(culture))


@router.get("/sysUser/export")
async def user_export(
    user: UserDep,
    page_size: int = Query(10000, le=10000),
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    result = await SysUserService(session, get_cache_service()).page(PageInput(page_index=1, page_size=page_size))
    headers = [
        ("id", "用户Id"),
        ("account", "账号"),
        ("real_name", "姓名"),
        ("status", "状态"),
        ("account_type", "账号类型"),
    ]
    content = export_xlsx(headers, [_dict(r, tuple(h[0] for h in headers)) for r in result.list])
    return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/sysPos/import")
async def pos_import(
    user: UserDep,
    file: UploadFile = File(...),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    content = await file.read()
    header_map = {"职位名称": "name", "职位编码": "code", "排序": "sort", "备注": "remark"}
    rows, errors = parse_xlsx(content, header_map)
    service = SysPosService(session)
    imported = 0
    for row in rows:
        if not row.get("name"):
            continue
        await service.add(row)
        imported += 1
    return success({"imported": imported, "errors": errors})
