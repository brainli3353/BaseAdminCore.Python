"""FastAPI 应用工厂。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.core.db.database import dispose_engines, get_session_factory
from src.core.db.schema import ensure_worker_id, init_schema
from src.core.job.scheduler import JobScheduler
from src.core.json import AdminJSONResponse
from src.core.services.file_service import UPLOAD_DIR
from src.web.api.router import api_router
from src.web.middleware import ExceptionMiddleware, PermissionMiddleware, TraceIdMiddleware

BASE_DIR = Path(__file__).resolve().parents[2]
WEB_DIST = BASE_DIR / "web" / "dist"
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import src.core.entities  # noqa: F401
    import src.core.job.scheduler  # noqa: F401
    import src.core.seeds.sys_config_seed  # noqa: F401
    import src.core.seeds.sys_dict_seed  # noqa: F401
    import src.core.seeds.sys_menu_seed  # noqa: F401
    import src.core.seeds.sys_org_seed  # noqa: F401
    import src.core.seeds.sys_pos_seed  # noqa: F401
    import src.core.seeds.sys_role_seed  # noqa: F401
    import src.core.seeds.sys_tenant_seed  # noqa: F401
    import src.core.seeds.sys_user_role_seed  # noqa: F401
    import src.core.seeds.sys_user_seed  # noqa: F401

    await init_schema()
    from src.core.realtime import init_realtime

    init_realtime()
    from src.core.config import get_settings

    await ensure_worker_id(get_settings().yit.worker_id)
    scheduler = JobScheduler(get_session_factory())
    await scheduler.start()
    yield
    await scheduler.stop()
    await dispose_engines()


def create_app() -> FastAPI:
    app = FastAPI(title="BaseAdminCore", version="0.1.0", default_response_class=AdminJSONResponse, lifespan=lifespan)
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(PermissionMiddleware)
    app.add_middleware(TraceIdMiddleware)

    app.include_router(api_router)

    (FRONTEND_DIR / "static").mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    @app.get("/health/live", tags=["health"])
    async def health_live() -> dict:
        return {"status": "live"}

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "healthy", "db": "unknown", "cache": "unknown"}

    @app.websocket("/ws")
    async def ws(websocket: WebSocket, token: str | None = None):
        from src.core.auth.jwt import verify_token
        from src.core.realtime import get_realtime

        user_id = None
        if token:
            try:
                user_id = int(verify_token(token).get("uid"))
            except Exception:
                user_id = None
        manager = get_realtime()
        if manager is None:
            await websocket.close()
            return
        await manager.connect(websocket, user_id)

    @app.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = WEB_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = WEB_DIST / "index.html"
        if index.is_file():
            return FileResponse(index)
        return FileResponse(FRONTEND_DIR / "templates" / "index.html")

    return app
