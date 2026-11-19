# BaseAdminCore（Python 版）

基础 Admin 框架的 Python 重写：FastAPI + SQLAlchemy 2.0（async/asyncpg）+ Pydantic v2 + Redis + 原生 JWT；前端为 Vue3 + Vite + Element Plus + vxe-table（pnpm，同源托管或独立 dev 代理）。

> 本仓对齐 .NET 上游 `BaseAdminCore.Net` 的功能面（81 功能点），按批推进。当前已落地：基础设施、认证（两阶段 OTP）、RBAC CRUD、Vue 前端骨架；系统服务域持续补齐。

## 目录

| 目录 | 落点 |
|---|---|
| `src/core` | 框架核心（实体基类/仓储/雪花/缓存/配置/异常/认证/RBAC/服务） |
| `src/web` | Web 支撑（FastAPI 应用工厂、中间件、依赖） |
| `src/entry` | 入口（`uvicorn` 启动） |
| `src/business` | 业务预留层（当前空） |
| `web/` | Vue3 + Vite 前端（pnpm） |
| `tests/` | pytest |
| `docs/` | 文档 |

## 运行

```powershell
uv sync --extra dev
uv run uvicorn src.entry.main:app --port 5090   # 后端 :5090，首次自动建表 + 种子

cd web; pnpm install; pnpm dev                  # 前端开发服务器 :5173（代理 /api → :5090）
cd web; pnpm build                              # 生产构建 → web/dist，由后端同源托管
```

默认账号 `admin` / `Admin@123` ＋ 动态码（TOTP）。

## 门

| 门 | 命令 |
|---|---|
| 后端静态 | `uv run ruff check src tests` |
| 后端测试 | `uv run pytest tests` |
| 前端 | `cd web; pnpm typecheck; pnpm build` |

## 实时通道

`/ws?token=<access>`（WebSocket），消息 `{kind, data}`：`onlineUserList` / `force_offline` / `public_notice` / `receive_message`。前端封装见 `web/src/utils/realtime.ts`。

## 文档

`docs/开发规范.md`（**业务开发唯一约定源**，约定 1–14）、`docs/README.md`（导航）、`docs/框架索引.md`（文件地图/机制）、`docs/框架使用指南.md`（cookbook）。
