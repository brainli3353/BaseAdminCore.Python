# BaseAdminCore（Python 版）文档导航

> 本仓是 .NET 上游 `BaseAdminCore.Net` 的 Python 重写，功能面对齐 81 功能点。

## 阅读路径

| 主题 | 位置 |
|---|---|
| 项目入口 / 运行 | 根 `README.md` |
| 框架文件地图与机制 | `docs/框架索引.md` |
| 业务开发 cookbook | `docs/框架使用指南.md` |

## 技术栈

- 后端：FastAPI + SQLAlchemy 2.0（async/asyncpg）+ Pydantic v2 + python-jose + pyotp + Redis
- 前端：Vue3 + Vite + Element Plus + vxe-table（pnpm）
- 数据库：PostgreSQL；缓存：Redis / Memory

## 门

| 门 | 命令 |
|---|---|
| 后端静态 | `uv run ruff check src tests` |
| 后端测试 | `uv run pytest tests` |
| 前端 | `cd web && pnpm typecheck && pnpm build` |
