"""JSON 出口单源：long → string（对齐上游 G33，防 JS 精度丢失）。"""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from starlette.responses import JSONResponse


def _convert(obj: Any) -> Any:
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, int):
        return str(obj) if abs(obj) > 9007199254740991 else obj
    if isinstance(obj, float):
        return obj
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat(sep=" ").replace("+00:00", "Z")
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, BaseModel):
        return _convert(obj.model_dump(mode="python", by_alias=True, exclude_none=False))
    if dataclasses.is_dataclass(obj):
        return _convert(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _convert(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_convert(v) for v in obj]
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    return obj


class AdminJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(_convert(content), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
