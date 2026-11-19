from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityBase, EntityTenant


class SysLogOp(EntityBase):
    __tablename__ = "sys_log_op"

    controller_name: Mapped[str | None] = mapped_column("ControllerName", String(64), nullable=True)
    action_name: Mapped[str | None] = mapped_column("ActionName", String(64), nullable=True)
    http_method: Mapped[str | None] = mapped_column("HttpMethod", String(16), nullable=True)
    remote_ip: Mapped[str | None] = mapped_column("RemoteIp", String(64), nullable=True)
    elapsed_ms: Mapped[int] = mapped_column("ElapsedMs", Integer, nullable=False, default=0, server_default=text("0"))
    account: Mapped[str | None] = mapped_column("Account", String(64), nullable=True)
    success: Mapped[bool] = mapped_column("Success", Boolean, nullable=False, default=True, server_default=text("true"))
    request_param: Mapped[str | None] = mapped_column("RequestParam", Text, nullable=True)
    return_result: Mapped[str | None] = mapped_column("ReturnResult", Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column("TraceId", String(64), nullable=True)


class SysLogEx(EntityBase):
    __tablename__ = "sys_log_ex"

    controller_name: Mapped[str | None] = mapped_column("ControllerName", String(64), nullable=True)
    action_name: Mapped[str | None] = mapped_column("ActionName", String(64), nullable=True)
    http_method: Mapped[str | None] = mapped_column("HttpMethod", String(16), nullable=True)
    request_url: Mapped[str | None] = mapped_column("RequestUrl", Text, nullable=True)
    request_param: Mapped[str | None] = mapped_column("RequestParam", Text, nullable=True)
    return_result: Mapped[str | None] = mapped_column("ReturnResult", Text, nullable=True)
    remote_ip: Mapped[str | None] = mapped_column("RemoteIp", String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column("TraceId", String(128), nullable=True)
    thread_id: Mapped[int | None] = mapped_column("ThreadId", Integer, nullable=True)
    account: Mapped[str | None] = mapped_column("Account", String(64), nullable=True)
    real_name: Mapped[str | None] = mapped_column("RealName", String(64), nullable=True)
    exception: Mapped[str | None] = mapped_column("Exception", Text, nullable=True)
    log_level: Mapped[str | None] = mapped_column("LogLevel", String(32), nullable=True)


class SysLogDiff(EntityTenant):
    __tablename__ = "sys_log_diff"

    before_data: Mapped[str | None] = mapped_column("BeforeData", Text, nullable=True)
    after_data: Mapped[str | None] = mapped_column("AfterData", Text, nullable=True)
    sql: Mapped[str | None] = mapped_column("Sql", Text, nullable=True)
    parameters: Mapped[str | None] = mapped_column("Parameters", Text, nullable=True)
    business_data: Mapped[str | None] = mapped_column("BusinessData", Text, nullable=True)
    diff_type: Mapped[str | None] = mapped_column("DiffType", String(16), nullable=True)
    elapsed: Mapped[int | None] = mapped_column("Elapsed", BigInteger, nullable=True)


class SysLogHttp(EntityBase):
    __tablename__ = "sys_log_http"

    http_method: Mapped[str | None] = mapped_column("HttpMethod", String(16), nullable=True)
    request_url: Mapped[str | None] = mapped_column("RequestUrl", String(1024), nullable=True)
    request_headers: Mapped[str | None] = mapped_column("RequestHeaders", Text, nullable=True)
    request_body: Mapped[str | None] = mapped_column("RequestBody", Text, nullable=True)
    status_code: Mapped[int | None] = mapped_column("StatusCode", Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column("ResponseBody", Text, nullable=True)
    elapsed_ms: Mapped[int | None] = mapped_column("ElapsedMs", BigInteger, nullable=True)
    has_exception: Mapped[bool] = mapped_column(
        "HasException", Boolean, nullable=False, default=False, server_default=text("false")
    )
    exception: Mapped[str | None] = mapped_column("Exception", Text, nullable=True)
    account: Mapped[str | None] = mapped_column("Account", String(64), nullable=True)
    real_name: Mapped[str | None] = mapped_column("RealName", String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column("TraceId", String(128), nullable=True)
