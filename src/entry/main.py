"""入口：uvicorn 启动。"""

from __future__ import annotations

import uvicorn

from src.web.app import create_app

app = create_app()


def main() -> None:
    uvicorn.run("src.entry.main:app", host="0.0.0.0", port=5090, reload=False)


if __name__ == "__main__":
    main()
