from __future__ import annotations

import io
from datetime import date, datetime

from openpyxl import Workbook


def export_xlsx(headers: list[tuple[str, str]], rows: list[dict]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append([header for _, header in headers])
    for row in rows:
        values = []
        for field, _ in headers:
            value = row.get(field)
            if isinstance(value, (datetime, date)):
                value = value.isoformat(sep=" ")
            values.append(value)
        sheet.append(values)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
