from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.constants import ErrorKeys
from src.core.db.repository import Repository
from src.core.entities.sys_file import SysFile, SysFileContent
from src.core.exceptions import AppException
from src.core.pagination import PageInput, PageResult

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path.cwd() / "uploads")))


class SysFileService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = Repository(session, SysFile)
        self._content_repo = Repository(session, SysFileContent)

    async def page(self, input: PageInput) -> PageResult[SysFile]:
        conditions = []
        if input.keyword:
            conditions.append(SysFile.file_name.ilike(f"%{input.keyword}%"))
        return await self._repo.page(input.page_index, input.page_size, *conditions, order_by=SysFile.id.desc())

    async def upload(self, file: UploadFile, provider: str = "Local", data_id: int | None = None) -> SysFile:
        content = await file.read()
        md5 = hashlib.md5(content).hexdigest()
        size_kb = (len(content) + 1023) // 1024
        existing = await self._repo.get_first(SysFile.file_md5 == md5, SysFile.size_kb == size_kb)
        if existing is not None:
            return existing
        suffix = (Path(file.filename or "").suffix or "").lower()
        allowed = [s.lower() for s in get_settings().upload.allow_suffix]
        if allowed and suffix.lstrip(".") not in allowed:
            raise AppException(ErrorKeys.FileForbidden, "不支持的文件类型")
        now = datetime.now()
        path_segment = f"{now.year}/{now.month}/{now.day}"
        row = SysFile(
            file_md5=md5,
            size_kb=size_kb,
            file_name=file.filename,
            file_path=path_segment,
            suffix=suffix,
            provider=provider,
            data_id=data_id,
        )
        await self._repo.add(row)
        if provider == "Db":
            await self._content_repo.add(SysFileContent(sys_file_id=row.id, content=content))
            row.url = f"/api/sysFile/download?id={row.id}&md5={md5}"
        else:
            directory = UPLOAD_DIR / path_segment
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{row.id}{suffix}").write_bytes(content)
            row.url = f"/uploads/{path_segment}/{row.id}{suffix}"
        await self._repo.update(row)
        return row

    async def download(self, file_id: int, md5: str | None = None) -> tuple[SysFile, bytes]:
        row = await self._repo.get_by_id(file_id)
        if row is None:
            raise AppException(ErrorKeys.FileNotFound, "文件不存在")
        if md5 and row.file_md5 != md5:
            raise AppException(ErrorKeys.FileForbidden, "文件校验失败")
        if row.provider == "Db":
            content = await self._content_repo.get_first(SysFileContent.sys_file_id == row.id)
            if content is None or content.content is None:
                raise AppException(ErrorKeys.FileNotFound, "文件内容不存在")
            return row, content.content
        path = UPLOAD_DIR / (row.file_path or "") / f"{row.id}{row.suffix or ''}"
        if not path.is_file():
            raise AppException(ErrorKeys.FileNotFound, "文件不存在")
        return row, path.read_bytes()

    async def delete(self, file_id: int) -> None:
        row = await self._repo.get_by_id(file_id)
        if row is None:
            raise AppException(ErrorKeys.FileNotFound, "文件不存在")
        await self._content_repo.session.execute(
            SysFileContent.__table__.delete().where(SysFileContent.sys_file_id == row.id)
        )
        await self._repo.delete(row)
