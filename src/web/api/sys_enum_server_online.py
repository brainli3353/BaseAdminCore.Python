from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_session
from src.core.responses import success
from src.core.services.enum_service import SysEnumService
from src.core.services.online_user_service import SysOnlineUserService
from src.core.services.server_service import SysServerService
from src.web.deps import UserDep, get_cache_service

router = APIRouter(tags=["enum-server-online"])


@router.get("/sysEnum/typeList")
async def enum_type_list(user: UserDep):
    return success(SysEnumService().get_type_list())


@router.get("/sysEnum/data")
async def enum_data(user: UserDep, enumName: str = Query(...)):
    return success(SysEnumService().get_data(enumName))


@router.get("/sysEnum/dataByField")
async def enum_data_by_field(user: UserDep, entityName: str = Query(...), fieldName: str = Query(...)):
    return success(SysEnumService().get_data_by_field(entityName, fieldName))


@router.get("/sysServer/runtime")
async def server_runtime(user: UserDep):
    return success(SysServerService().get_runtime())


@router.get("/sysServer/hardware")
async def server_hardware(user: UserDep):
    return success(SysServerService().get_hardware())


@router.get("/sysServer/assembly")
async def server_assembly(user: UserDep):
    return success(SysServerService().get_assemblies())


@router.get("/sysServer/nodes")
async def server_nodes(user: UserDep):
    return success(SysServerService().get_nodes())


@router.get("/onlineUser/list")
async def online_list(
    user: UserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    service = SysOnlineUserService(get_cache_service())
    return success(await service.list(user))


@router.post("/onlineUser/forceOffline")
async def online_force_offline(
    body: dict,
    user: UserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    service = SysOnlineUserService(get_cache_service())
    await service.force_offline(int(body["userId"]))
    return success()
