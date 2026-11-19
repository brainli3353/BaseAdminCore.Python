"""配置链（对齐上游：模块 JSON → 环境变量 → 命令行；此处先落地 env/.env，JSON 模块链预留）。

 环境变量用双下划线代替冒号（pydantic-settings env_nested_delimiter）。
 生产密钥只经环境变量注入；仓库内值一律本地开发占位。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class AppOptions:
    name: str = "BaseAdminCore"
    full_name: str | None = None
    title_suffix: str | None = None


@dataclass
class DbSettingsOptions:
    enable_incre_table: bool = True
    slow_sql_seconds: float = 5.0


@dataclass
class CacheOptions:
    type: Literal["Redis", "Memory"] = "Memory"


@dataclass
class JwtOptions:
    secret: str = "CHANGE_ME__local_dev_secret__min_32_chars"
    issuer: str = "BaseAdminCore"
    audience: str = "BaseAdminCore"
    expire_hours: int = 8
    refresh_token_expire_hours: int = 168


@dataclass
class OtpOptions:
    issuer: str = "BaseAdminCore"


@dataclass
class YitOptions:
    worker_id: int = 1


@dataclass
class SysPasswordOptions:
    strength_expression: str | None = None
    expiration_days: int = 0


@dataclass
class CryptogramOptions:
    key: str | None = None


@dataclass
class UploadOptions:
    content_type: list[str] = field(default_factory=list)
    allow_suffix: list[str] = field(default_factory=lambda: ["jpg", "png", "gif", "pdf", "xlsx", "docx", "zip"])


@dataclass
class HttpLogOptions:
    enabled: bool = False
    max_body_length: int = 2048
    exclude_hosts: list[str] = field(default_factory=list)
    mask_headers: list[str] = field(default_factory=list)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    environment: str = "Development"
    app_name: str = "BaseAdminCore"
    app_full_name: str | None = None
    app_title_suffix: str | None = None

    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_database: str = "huluyeye_admin"
    log_db_database: str = "huluyeye_admin"

    redis_connectionstring: str = ""
    cache_type: Literal["Redis", "Memory"] = "Memory"

    jwt_secret: str = "CHANGE_ME__local_dev_secret__min_32_chars"
    jwt_issuer: str = "BaseAdminCore"
    jwt_audience: str = "BaseAdminCore"
    jwt_expire_hours: int = 8
    jwt_refresh_token_expire_hours: int = 168

    otp_issuer: str = "BaseAdminCore"
    yit_worker_id: int = 1
    sys_password_strength_expression: str | None = None
    sys_password_expiration_days: int = 0
    cryptogram_key: str | None = None

    db_settings_enable_incre_table: bool = True
    db_settings_slow_sql_seconds: float = 5.0

    upload_allow_suffix: str = "jpg,png,gif,pdf,xlsx,docx,zip"

    logging_http_enabled: bool = False
    logging_http_max_body_length: int = 2048

    @property
    def app(self) -> AppOptions:
        full_name = self.app_full_name or None
        return AppOptions(name=self.app_name, full_name=full_name, title_suffix=self.app_title_suffix or None)

    @property
    def db(self) -> DbSettingsOptions:
        return DbSettingsOptions(
            enable_incre_table=self.db_settings_enable_incre_table,
            slow_sql_seconds=self.db_settings_slow_sql_seconds,
        )

    @property
    def cache(self) -> CacheOptions:
        return CacheOptions(type=self.cache_type)

    @property
    def jwt(self) -> JwtOptions:
        expire = self.jwt_expire_hours if self.jwt_expire_hours > 0 else 8
        refresh = self.jwt_refresh_token_expire_hours if self.jwt_refresh_token_expire_hours > 0 else 168
        return JwtOptions(
            secret=self.jwt_secret,
            issuer=self.jwt_issuer,
            audience=self.jwt_audience,
            expire_hours=expire,
            refresh_token_expire_hours=refresh,
        )

    @property
    def otp(self) -> OtpOptions:
        return OtpOptions(issuer=self.otp_issuer or self.app_name)

    @property
    def yit(self) -> YitOptions:
        return YitOptions(worker_id=self.yit_worker_id)

    @property
    def sys_password(self) -> SysPasswordOptions:
        return SysPasswordOptions(
            strength_expression=self.sys_password_strength_expression,
            expiration_days=self.sys_password_expiration_days,
        )

    @property
    def cryptogram(self) -> CryptogramOptions:
        return CryptogramOptions(key=self.cryptogram_key)

    @property
    def upload(self) -> UploadOptions:
        return UploadOptions(allow_suffix=[s.strip() for s in self.upload_allow_suffix.split(",") if s.strip()])

    @property
    def http_log(self) -> HttpLogOptions:
        return HttpLogOptions(
            enabled=self.logging_http_enabled,
            max_body_length=self.logging_http_max_body_length,
        )

    def main_connection_string(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )

    def log_connection_string(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.log_db_database}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "Development").lower() == "production"
