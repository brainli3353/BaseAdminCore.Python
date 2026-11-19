from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from fastapi import WebSocket

logger = logging.getLogger("admincore.realtime")

Handler = Callable[[dict], Awaitable[None] | None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, kind: str, handler: Handler) -> None:
        self._handlers.setdefault(kind, []).append(handler)

    async def publish(self, kind: str, payload: dict) -> None:
        for handler in self._handlers.get(kind, []):
            try:
                result = handler(payload)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("事件处理失败: %s", kind)


class RealtimeManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self._clients: dict[WebSocket, int | None] = {}

    async def connect(self, websocket: WebSocket, user_id: int | None) -> None:
        await websocket.accept()
        self._clients[websocket] = user_id
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            pass
        finally:
            self._clients.pop(websocket, None)

    async def broadcast(self, kind: str, payload: dict) -> None:
        message = json.dumps({"kind": kind, "data": payload}, ensure_ascii=False)
        for client in list(self._clients):
            try:
                await client.send_text(message)
            except Exception:
                self._clients.pop(client, None)

    async def send_to_user(self, user_id: int, kind: str, payload: dict) -> None:
        message = json.dumps({"kind": kind, "data": payload}, ensure_ascii=False)
        for client, owner in list(self._clients.items()):
            if owner != user_id:
                continue
            try:
                await client.send_text(message)
            except Exception:
                self._clients.pop(client, None)

    def register_bus(self) -> None:
        self._bus.subscribe("online_push", lambda p: self.broadcast(p.get("kind", "online_push"), p.get("data", {})))
        self._bus.subscribe("force_offline", lambda p: self.broadcast("force_offline", p))
        self._bus.subscribe("public_notice", lambda p: self.broadcast("public_notice", p))
        self._bus.subscribe("receive_message", lambda p: self.broadcast("receive_message", p))


_realtime: RealtimeManager | None = None


def get_realtime() -> RealtimeManager | None:
    return _realtime


def init_realtime() -> RealtimeManager:
    global _realtime
    bus = EventBus()
    _realtime = RealtimeManager(bus)
    _realtime.register_bus()
    return _realtime


async def publish_event(kind: str, payload: dict) -> None:
    manager = get_realtime()
    if manager is not None:
        await manager._bus.publish(kind, payload)
