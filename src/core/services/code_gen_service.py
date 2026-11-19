from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AppException
from src.core.services.database_service import SysDatabaseService

TYPE_MAP = {
    "character varying": "string",
    "character": "string",
    "text": "string",
    "json": "string",
    "xml": "string",
    "bigint": "long",
    "int8": "long",
    "integer": "int",
    "int4": "int",
    "smallint": "int",
    "int2": "int",
    "boolean": "bool",
    "timestamp without time zone": "DateTime",
    "timestamp with time zone": "DateTime",
    "date": "DateTime",
    "numeric": "decimal",
    "decimal": "decimal",
    "money": "decimal",
    "double precision": "double",
    "float8": "double",
    "real": "float",
    "float4": "float",
    "uuid": "Guid",
    "bytea": "byte[]",
}

AUDIT_COLUMNS = {"Id", "CreateTime", "CreateUserId", "CreateUserName", "UpdateTime", "UpdateUserId", "UpdateUserName", "DeleteTime", "IsDelete", "TenantId"}


class CodeGenService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = SysDatabaseService()

    async def get_table_list(self, keyword: str | None = None) -> list[dict]:
        return await self._db.list_tables(keyword)

    async def preview(self, table_name: str, class_name: str | None, module_name: str, remove_prefix: str, base_type: str) -> dict:
        if not table_name:
            raise AppException("codegen.table_required", "表名必填")
        columns = await self._db.list_columns(table_name)
        class_name = class_name or _pascal(_remove_prefix(table_name, remove_prefix))
        entity = _render_entity(table_name, class_name, columns, base_type)
        dtos = _render_dtos(class_name)
        service = _render_service(class_name, module_name)
        return {"entity": entity, "dtos": dtos, "service": service, "warnings": []}


def _remove_prefix(table: str, prefix: str) -> str:
    if prefix and table.startswith(prefix):
        return table[len(prefix):]
    return table


def _pascal(name: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_\-]", name) if part)


def _render_entity(table: str, class_name: str, columns: list[dict], base_type: str) -> str:
    lines = [f'[SugarTable("{table}")]']
    lines.append(f"public class {class_name} : {base_type or 'EntityBase'}")
    lines.append("{")
    for col in columns:
        name = col["Name"]
        if name in AUDIT_COLUMNS:
            continue
        cs_type = TYPE_MAP.get(col["Type"], "string")
        nullable = "" if col["NotNull"] else "?"
        lines.append(f'    [SugarColumn(ColumnDescription = "{col.get("Comment") or name}")]')
        lines.append(f"    public {cs_type}{nullable} {_pascal(name)} {{ get; set; }}")
    lines.append("}")
    return "\n".join(lines)


def _render_dtos(class_name: str) -> str:
    return (
        f"public record Page{class_name}Input : PageInputBase;\n\n"
        f"public record {class_name}Output(long Id, string Name);\n\n"
        f"public record Add{class_name}Input;\n\n"
        f"public record Update{class_name}Input(long Id);"
    )


def _render_service(class_name: str, module_name: str) -> str:
    return (
        f"[Service]\npublic class {class_name}Service\n{{\n"
        f"    public async Task<PageResult<{class_name}Output>> PageAsync(Page{class_name}Input input)\n"
        f"    {{\n        // 逐字段判 null 后赋值（禁止整对象覆盖）\n    }}\n}}"
    )
