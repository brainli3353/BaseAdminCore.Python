from __future__ import annotations

from sqlalchemy import BigInteger, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import EntityBase, EntityBaseOrg


class SysFile(EntityBaseOrg):
    __tablename__ = "sys_file"

    file_md5: Mapped[str | None] = mapped_column("FileMd5", String(32), nullable=True)
    size_kb: Mapped[int] = mapped_column("SizeKb", BigInteger, nullable=False, default=0)
    file_name: Mapped[str | None] = mapped_column("FileName", String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column("FilePath", String(64), nullable=True)
    suffix: Mapped[str | None] = mapped_column("Suffix", String(32), nullable=True)
    provider: Mapped[str | None] = mapped_column("Provider", String(16), nullable=True)
    data_id: Mapped[int | None] = mapped_column("DataId", BigInteger, nullable=True)
    url: Mapped[str | None] = mapped_column("Url", String(512), nullable=True)


class SysFileContent(EntityBase):
    __tablename__ = "sys_file_content"

    sys_file_id: Mapped[int] = mapped_column("SysFileId", BigInteger, nullable=False)
    content: Mapped[bytes | None] = mapped_column("Content", LargeBinary, nullable=True)
