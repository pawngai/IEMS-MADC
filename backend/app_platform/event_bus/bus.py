from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from app_platform.event_bus.types import BaseEvent


EventHandler = Callable[[BaseEvent], Awaitable[None] | None]


class EventBus:
    def __init__(self) -> None:
        self._subscriptions: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._subscriptions[event_name].append(handler)

    async def publish(self, event: BaseEvent) -> None:
        handlers = self._subscriptions.get(event.name, [])
        for handler in handlers:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
