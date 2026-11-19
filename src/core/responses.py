"""统一响应体 ApiResult：{code, errCode, msg, data}（HTTP 恒 200）。"""

from __future__ import annotations

from typing import Any

from src.core.constants import ErrorCodes


def success(data: Any = None, msg: str = "操作成功", code: int = ErrorCodes.Success) -> dict[str, Any]:
    return {"code": code, "errCode": None, "msg": msg, "data": data}


def fail(
    msg: str = "操作失败",
    code: int = ErrorCodes.Fail,
    err_code: str | None = None,
    data: Any = None,
) -> dict[str, Any]:
    return {"code": code, "errCode": err_code, "msg": msg, "data": data}
