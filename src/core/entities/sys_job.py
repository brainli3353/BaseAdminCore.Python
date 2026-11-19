from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityTenant


class SysJobDetail(EntityTenant):
    __tablename__ = "sys_job_detail"

    job_name: Mapped[str | None] = mapped_column("JobName", String(64), nullable=True)
    interval: Mapped[int] = mapped_column(
        "Interval", Integer, nullable=False, default=3600, server_default=text("3600")
    )
    enabled: Mapped[bool] = mapped_column("Enabled", Boolean, nullable=False, default=True, server_default=text("true"))
    last_run_time: Mapped[datetime | None] = mapped_column("LastRunTime", DateTime(timezone=True), nullable=True)
    remark: Mapped[str | None] = mapped_column("Remark", String(256), nullable=True)
    target_node: Mapped[str | None] = mapped_column("TargetNode", String(128), nullable=True)


class SysJobLog(EntityTenant):
    __tablename__ = "sys_job_log"

    job_name: Mapped[str] = mapped_column("JobName", String(64), nullable=False, default="")
    trigger: Mapped[str] = mapped_column("Trigger", String(16), nullable=False, default="")
    triggered_at: Mapped[datetime] = mapped_column("TriggeredAt", DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(
        "DurationMs", BigInteger, nullable=False, default=0, server_default=text("0")
    )
    success: Mapped[bool] = mapped_column("Success", Boolean, nullable=False, default=True, server_default=text("true"))
    error_msg: Mapped[str | None] = mapped_column("ErrorMsg", String(512), nullable=True)
    instance_id: Mapped[str] = mapped_column("InstanceId", String(64), nullable=False, default="")
    node_tag: Mapped[str | None] = mapped_column("NodeTag", String(128), nullable=True)
