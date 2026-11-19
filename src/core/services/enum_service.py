from __future__ import annotations

import importlib
import inspect
from enum import Enum

from src.core.exceptions import AppException


class SysEnumService:
    def get_type_list(self) -> list[dict]:
        module = importlib.import_module("src.core.enums")
        result = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Enum) and obj.__module__ == module.__name__:
                result.append({"name": name, "values": self._values(obj)})
        return result

    def get_data(self, enum_name: str) -> list[dict]:
        module = importlib.import_module("src.core.enums")
        obj = getattr(module, enum_name, None)
        if obj is None or not issubclass(obj, Enum):
            raise AppException("enum.not_found", "枚举不存在")
        return self._values(obj)

    def get_data_by_field(self, entity_name: str, field_name: str) -> list[dict]:
        return []

    def _values(self, enum_cls: type[Enum]) -> list[dict]:
        result = []
        for member in enum_cls:
            value = member.value
            result.append({"name": member.name, "value": value})
        return result
