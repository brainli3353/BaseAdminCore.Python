from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.pagination import PageInput
from src.core.responses import success
from src.core.services.file_service import SysFileService
from src.core.services.job_service import SysJobService
from src.core.services.log_service import SysLogService
from src.web.deps import UserDep

router = APIRouter(tags=["log-job-file"])


def _log_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysLogService:
    return SysLogService(session)


def _job_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysJobService:
    return SysJobService(session)


def _file_service(session: Annotated[AsyncSession, Depends(get_session)]) -> SysFileService:
    return SysFileService(session)


def _page(
    page_index: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: str | None = Query(None),
) -> PageInput:
    return PageInput(page_index=page_index, page_size=page_size, keyword=keyword)


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


LOGIN_FIELDS = ("id", "account", "remote_addr", "status", "message", "login_type", "create_time")
OP_FIELDS = (
    "id",
    "controller_name",
    "action_name",
    "http_method",
    "remote_ip",
    "elapsed_ms",
    "account",
    "success",
    "trace_id",
)
EX_FIELDS = (
    "id",
    "controller_name",
    "action_name",
    "http_method",
    "request_url",
    "remote_ip",
    "trace_id",
    "account",
    "real_name",
    "log_level",
)
DIFF_FIELDS = ("id", "diff_type", "business_data", "elapsed", "create_time")
HTTP_FIELDS = (
    "id",
    "http_method",
    "request_url",
    "status_code",
    "elapsed_ms",
    "has_exception",
    "account",
    "trace_id",
)
JOB_FIELDS = ("id", "job_name", "interval", "enabled", "last_run_time", "remark", "target_node")
JOB_LOG_FIELDS = (
    "id",
    "job_name",
    "trigger",
    "triggered_at",
    "duration_ms",
    "success",
    "error_msg",
    "instance_id",
    "node_tag",
)
FILE_FIELDS = ("id", "file_md5", "size_kb", "file_name", "file_path", "suffix", "provider", "data_id", "url")


def _dict(obj, fields: tuple[str, ...]) -> dict:
    return {field: getattr(obj, field, None) for field in fields}


@router.get("/sysLogLogin/page")
async def log_login_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    account: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    result = await service.page_login(page, account, _ts(start_time), _ts(end_time))
    return success({"total": result.total, "list": [_dict(r, LOGIN_FIELDS) for r in result.list]})


@router.get("/sysLogOp/page")
async def log_op_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    account: str | None = Query(None),
    controller: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    result = await service.page_op(page, account, controller, _ts(start_time), _ts(end_time))
    return success({"total": result.total, "list": [_dict(r, OP_FIELDS) for r in result.list]})


@router.get("/sysLogOp/detail")
async def log_op_detail(
    user: UserDep,
    id: int = Query(...),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    row = await service.detail_op(id)
    return success(_dict(row, OP_FIELDS + ("request_param", "return_result")) if row else None)


@router.get("/sysLogEx/page")
async def log_ex_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    account: str | None = Query(None),
    remote_ip: str | None = Query(None),
    controller: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    result = await service.page_ex(page, account, remote_ip, controller, _ts(start_time), _ts(end_time))
    return success({"total": result.total, "list": [_dict(r, EX_FIELDS) for r in result.list]})


@router.get("/sysLogEx/detail")
async def log_ex_detail(
    user: UserDep,
    id: int = Query(...),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    row = await service.detail_ex(id)
    fields = EX_FIELDS + ("request_param", "return_result", "exception", "thread_id")
    return success(_dict(row, fields) if row else None)


@router.get("/sysLogDiff/page")
async def log_diff_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    result = await service.page_diff(page, _ts(start_time), _ts(end_time))
    return success({"total": result.total, "list": [_dict(r, DIFF_FIELDS) for r in result.list]})


@router.get("/sysLogDiff/detail")
async def log_diff_detail(
    user: UserDep,
    id: int = Query(...),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    row = await service.detail_diff(id)
    return success(_dict(row, DIFF_FIELDS + ("before_data", "after_data", "sql", "parameters")) if row else None)


@router.get("/sysLogHttp/page")
async def log_http_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    account: str | None = Query(None),
    url: str | None = Query(None),
    http_method: str | None = Query(None),
    status_code: int | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    result = await service.page_http(
        page, account, url, http_method, status_code, _ts(start_time), _ts(end_time)
    )
    return success({"total": result.total, "list": [_dict(r, HTTP_FIELDS) for r in result.list]})


@router.get("/sysLogHttp/detail")
async def log_http_detail(
    user: UserDep,
    id: int = Query(...),
    service: SysLogService = Depends(_log_service),  # noqa: B008
):
    row = await service.detail_http(id)
    return success(
        _dict(row, HTTP_FIELDS + ("request_headers", "request_body", "response_body", "exception")) if row else None
    )


@router.get("/sysJob/page")
async def job_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysJobService = Depends(_job_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(r, JOB_FIELDS) for r in result.list]})


@router.post("/sysJob/add")
async def job_add(body: dict, user: UserDep, service: SysJobService = Depends(_job_service)):  # noqa: B008
    return success(_dict(await service.add(body), JOB_FIELDS))


@router.post("/sysJob/update")
async def job_update(body: dict, user: UserDep, service: SysJobService = Depends(_job_service)):  # noqa: B008
    return success(_dict(await service.update(int(body["id"]), body), JOB_FIELDS))


@router.post("/sysJob/enable")
async def job_enable(body: dict, user: UserDep, service: SysJobService = Depends(_job_service)):  # noqa: B008
    await service.set_enabled(int(body["id"]), True)
    return success()


@router.post("/sysJob/disable")
async def job_disable(body: dict, user: UserDep, service: SysJobService = Depends(_job_service)):  # noqa: B008
    await service.set_enabled(int(body["id"]), False)
    return success()


@router.post("/sysJob/runNow")
async def job_run_now(body: dict, user: UserDep, service: SysJobService = Depends(_job_service)):  # noqa: B008
    await service.run_now(int(body["id"]))
    return success()


@router.get("/sysJob/logPage")
async def job_log_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    job_name: str | None = Query(None),
    service: SysJobService = Depends(_job_service),  # noqa: B008
):
    result = await service.page_log(page, job_name)
    return success({"total": result.total, "list": [_dict(r, JOB_LOG_FIELDS) for r in result.list]})


@router.get("/sysFile/page")
async def file_page(
    user: UserDep,
    page: Annotated[PageInput, Depends(_page)],
    service: SysFileService = Depends(_file_service),  # noqa: B008
):
    result = await service.page(page)
    return success({"total": result.total, "list": [_dict(r, FILE_FIELDS) for r in result.list]})


@router.post("/sysFile/upload")
async def file_upload(
    user: UserDep,
    file: UploadFile = File(...),  # noqa: B008
    provider: str = Form("Local"),  # noqa: B008
    service: SysFileService = Depends(_file_service),  # noqa: B008
):
    row = await service.upload(file, provider=provider)
    return success(_dict(row, FILE_FIELDS))


@router.get("/sysFile/download")
async def file_download(
    user: UserDep,
    id: int = Query(...),
    md5: str | None = Query(None),
    service: SysFileService = Depends(_file_service),  # noqa: B008
):
    row, content = await service.download(id, md5)
    filename = row.file_name or f"{row.id}{row.suffix or ''}"
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.post("/sysFile/delete")
async def file_delete(body: dict, user: UserDep, service: SysFileService = Depends(_file_service)):  # noqa: B008
    await service.delete(int(body["id"]))
    return success()
