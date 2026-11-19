from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.context import get_current_user
from src.core.db.filters import apply_filters
from src.core.pagination import PageResult

T = TypeVar("T")

_UNSET = object()


class Repository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model
        self._org_scope: object = _UNSET

    async def _scope(self) -> tuple[str, object] | None:
        if self._org_scope is not _UNSET:
            return self._org_scope  # type: ignore[return-value]
        if not hasattr(self.model, "create_org_id"):
            self._org_scope = None
        else:
            from src.core.security.data_scope import compute_data_scope

            self._org_scope = await compute_data_scope(self.session, get_current_user())
        return self._org_scope  # type: ignore[return-value]

    async def get_by_id(self, entity_id: int, *, include_deleted: bool = False) -> T | None:
        stmt = select(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        stmt = apply_filters(stmt, self.model, include_deleted=include_deleted, org_scope=await self._scope())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_first(self, *conditions: Any, include_deleted: bool = False) -> T | None:
        stmt = select(self.model)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = apply_filters(stmt, self.model, include_deleted=include_deleted, org_scope=await self._scope())
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def list(
        self,
        *conditions: Any,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int | None = None,
        order_by: Any = None,
    ) -> Sequence[T]:
        stmt = select(self.model)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = apply_filters(stmt, self.model, include_deleted=include_deleted, org_scope=await self._scope())
        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)
        if skip:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def page(
        self,
        page_index: int = 1,
        page_size: int = 10,
        *conditions: Any,
        order_by: Any = None,
        include_deleted: bool = False,
    ) -> PageResult[T]:
        scope = await self._scope()
        base = select(self.model)
        if conditions:
            base = base.where(*conditions)
        base = apply_filters(base, self.model, include_deleted=include_deleted, org_scope=scope)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()
        stmt = base
        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)
        stmt = stmt.offset((page_index - 1) * page_size).limit(page_size)
        rows = (await self.session.execute(stmt)).scalars().all()
        return PageResult(total=int(total), list=list(rows), page_index=page_index, page_size=page_size)

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def add_range(self, entities: Sequence[T]) -> None:
        self.session.add_all(entities)
        await self.session.flush()

    async def update(self, entity: T) -> T:
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def soft_delete(self, entity: T) -> None:
        entity.is_delete = True  # type: ignore[attr-defined]
        await self.session.flush()

    async def count(self, *conditions: Any, include_deleted: bool = False) -> int:
        stmt = select(func.count()).select_from(self.model)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = apply_filters(stmt, self.model, include_deleted=include_deleted, org_scope=await self._scope())
        return int((await self.session.execute(stmt)).scalar_one())

    async def exists(self, *conditions: Any, include_deleted: bool = False) -> bool:
        return await self.count(*conditions, include_deleted=include_deleted) > 0
