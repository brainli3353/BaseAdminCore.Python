from __future__ import annotations

from sqlalchemy import text

from src.core.db.database import get_engine
from src.core.exceptions import AppException


class SysDatabaseService:
    async def list_tables(self, keyword: str | None = None) -> list[dict]:
        sql = """
        SELECT c.relname AS "Name",
               obj_description(c.oid) AS "Comment",
               COALESCE(s.n_live_tup, 0) AS "RowCount",
               pg_size_pretty(pg_total_relation_size(c.oid)) AS "Size"
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
        WHERE n.nspname = 'public' AND c.relkind = 'r'
        """
        params: dict = {}
        if keyword:
            sql += " AND c.relname ILIKE :kw"
            params["kw"] = f"%{keyword}%"
        sql += " ORDER BY pg_total_relation_size(c.oid) DESC"
        async with get_engine().connect() as conn:
            rows = (await conn.execute(text(sql), params)).mappings().all()
        return [dict(r) for r in rows]

    async def list_columns(self, table: str) -> list[dict]:
        sql = """
        SELECT a.attname AS "Name", format_type(a.atttypid, a.atttypmod) AS "Type",
               a.attnotnull AS "NotNull", pg_get_expr(d.adbin, d.adrelid) AS "Default",
               col_description(a.attrelid, a.attnum) AS "Comment", a.attnum AS "Order"
        FROM pg_attribute a
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE a.attrelid = :table::regclass AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum
        """
        async with get_engine().connect() as conn:
            exists = (
                await conn.execute(
                    text("SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname=:t"),
                    {"t": table},
                )
            ).first()
            if exists is None:
                raise AppException("database.table_not_found", "表不存在")
            rows = (await conn.execute(text(sql), {"table": table})).mappings().all()
        return [dict(r) for r in rows]

    async def list_indexes(self, table: str) -> list[dict]:
        sql = """
        SELECT i.relname AS "Name", pg_get_indexdef(i.oid) AS "Definition",
               ix.indisunique AS "IsUnique", ix.indisprimary AS "IsPrimary"
        FROM pg_class t
        JOIN pg_index ix ON ix.indrelid = t.oid
        JOIN pg_class i ON i.oid = ix.indexrelid
        WHERE t.relname = :table
        ORDER BY ix.indisprimary DESC, i.relname
        """
        async with get_engine().connect() as conn:
            exists = (
                await conn.execute(
                    text("SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname=:t"),
                    {"t": table},
                )
            ).first()
            if exists is None:
                raise AppException("database.table_not_found", "表不存在")
            rows = (await conn.execute(text(sql), {"table": table})).mappings().all()
        return [dict(r) for r in rows]
