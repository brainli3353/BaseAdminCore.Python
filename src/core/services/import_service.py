from __future__ import annotations

from io import BytesIO

from openpyxl import load_workbook

MAX_ROWS = 5000
MAX_ERRORS = 100


def parse_xlsx(content: bytes, header_map: dict[str, str]) -> tuple[list[dict], list[str]]:
    workbook = load_workbook(filename=BytesIO(content), read_only=True, data_only=True)
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    try:
        header = next(rows)
    except StopIteration:
        return [], ["空文件"]
    index_map: dict[int, str] = {}
    for idx, title in enumerate(header):
        if title in header_map:
            index_map[idx] = header_map[title]
    result: list[dict] = []
    errors: list[str] = []
    for _row_number, row in enumerate(rows, start=2):
        if len(result) >= MAX_ROWS:
            errors.append(f"超过最大行数 {MAX_ROWS}")
            break
        item = {}
        for idx, field in index_map.items():
            item[field] = row[idx] if idx < len(row) else None
        result.append(item)
        if len(errors) >= MAX_ERRORS:
            break
    return result, errors
