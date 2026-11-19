from __future__ import annotations

from fastapi import APIRouter

from src.web.api.auth import router as auth_router
from src.web.api.rbac import router as rbac_router
from src.web.api.sys_dict_config import router as dict_config_router
from src.web.api.sys_enum_server_online import router as enum_server_router
from src.web.api.sys_log_job_file import router as log_job_file_router
from src.web.api.sys_notice_message import router as notice_message_router
from src.web.api.sys_tenant_open import router as tenant_open_router
from src.web.api.sys_tooling import router as tooling_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(rbac_router)
api_router.include_router(dict_config_router)
api_router.include_router(log_job_file_router)
api_router.include_router(notice_message_router)
api_router.include_router(tenant_open_router)
api_router.include_router(enum_server_router)
api_router.include_router(tooling_router)
