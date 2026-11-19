"""分页模型：PageInput / PageResult（对齐上游 ToPagedListAsync 契约）。"""

from __future__ import annotations

import builtins
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 10


class PageInput(BaseModel):
    page_index: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, description="每页条数，最大 200")
    keyword: str | None = Field(default=None, description="模糊关键字")

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        if self.page_size > MAX_PAGE_SIZE:
            self.page_size = MAX_PAGE_SIZE

    @property
    def skip(self) -> int:
        return (self.page_index - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PageResult(BaseModel, Generic[T]):
    model_config = {"populate_by_name": True}

    total: int = 0
    rows: builtins.list[T] = Field(default_factory=list, serialization_alias="list")
    page_index: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    @property
    def list(self) -> builtins.list[T]:
        return self.rows
