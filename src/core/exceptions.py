"""业务异常与错误码（对齐 .NET 上游 AppException/ErrorCodes 口径）。"""

from __future__ import annotations

from typing import Any

ErrorCodesFail = 1


class AppException(Exception):
    """业务异常：HTTP 恒 200，响应体携带 code/errCode/msg。"""

    def __init__(
        self,
        err_code: str | int | None = None,
        msg: str = "操作失败",
        code: int = ErrorCodesFail,
        http_status: int = 200,
        data: Any = None,
    ) -> None:
        super().__init__(msg)
        self.err_code = err_code
        self.msg = msg
        self.code = code
        self.http_status = http_status
        self.data = data

    @classmethod
    def of(cls, err_code: str, *args: Any, msg: str | None = None, code: int | None = None) -> AppException:
        template = msg or err_code
        if args:
            try:
                template = template.format(*args)
            except (IndexError, KeyError):
                pass
        return cls(err_code=err_code, msg=template, code=code if code is not None else 1)


class BadRequestException(AppException):
    def __init__(self, msg: str = "参数错误", err_code: str | None = None) -> None:
        super().__init__(err_code=err_code or "common.param_invalid", msg=msg, code=400)


class UnauthorizedException(AppException):
    def __init__(self, msg: str = "未登录或登录已失效", err_code: str | None = None) -> None:
        super().__init__(err_code=err_code or "common.unauthorized", msg=msg, code=401, http_status=401)


class ForbiddenException(AppException):
    def __init__(self, msg: str = "无权限", err_code: str | None = None) -> None:
        super().__init__(err_code=err_code or "common.forbidden", msg=msg, code=403, http_status=403)


class NotFoundException(AppException):
    def __init__(self, msg: str = "数据不存在", err_code: str | None = None) -> None:
        super().__init__(err_code=err_code or "common.not_found", msg=msg, code=404)


class ConflictException(AppException):
    def __init__(self, msg: str = "数据冲突", err_code: str | None = None) -> None:
        super().__init__(err_code=err_code or "common.conflict", msg=msg, code=409)
