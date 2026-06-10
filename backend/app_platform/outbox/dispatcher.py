from __future__ import annotations

import asyncio
import logging

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent
from app_platform.outbox.repo import OutboxRepository


logger = logging.getLogger(__name__)


class OutboxDispatcher:
    def __init__(
        self,
        *,
        outbox_repo: OutboxRepository,
        event_bus: EventBus,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 50,
        max_attempts: int = 5,
    ) -> None:
        self._outbox_repo = outbox_repo
        self._event_bus = event_bus
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size
        self._max_attempts = max_attempts
        self._task: asyncio.Task | None = None
        self._running = False

    async def _drain_once(self) -> None:
        pending = await self._outbox_repo.get_pending(
            self._batch_size,
            max_attempts=self._max_attempts,
        )
        for doc in pending:
            event_id = doc.get("_id")
            if not event_id:
                continue
            locked = await self._outbox_repo.lock_for_processing(event_id, ttl_seconds=30)
            if not locked:
                continue
            event = BaseEvent(
                event_id=event_id,
                name=doc.get("name", "UnknownEvent"),
                event_version=doc.get("event_version") or "v1",
                occurred_at=doc.get("occurred_at"),
                actor_id=doc.get("actor_id"),
                department_id=doc.get("department_id"),
                correlation_id=doc.get("correlation_id"),
                idempotency_key=doc.get("idempotency_key"),
                payload=doc.get("payload") or {},
            )
            try:
                await self._event_bus.publish(event)
                await self._outbox_repo.mark_sent(event_id)
            except Exception as exc:  # pragma: no cover
                logger.exception("Outbox dispatch failed for %s", event_id)
                await self._outbox_repo.mark_failed(
                    event_id,
                    str(exc),
                    max_attempts=self._max_attempts,
                )

    async def run_forever(self) -> None:
        self._running = True
        while self._running:
            await self._drain_once()
            await asyncio.sleep(self._poll_interval_seconds)

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_forever())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def replay_sent(
        self,
        *,
        event_names: list[str] | None = None,
        batch_size: int = 500,
    ) -> int:
        """Re-dispatch already-sent outbox events through the event bus.

        Subscribers must be idempotent — projections should use
        ``source_event_id`` to deduplicate.  Returns the count of
        events replayed.
        """
        docs = await self._outbox_repo.get_sent(
            event_names=event_names,
            batch_size=batch_size,
        )
        replayed = 0
        for doc in docs:
            event_id = doc.get("_id")
            if not event_id:
                continue
            event = BaseEvent(
                event_id=event_id,
                name=doc.get("name", "UnknownEvent"),
                event_version=doc.get("event_version") or "v1",
                occurred_at=doc.get("occurred_at"),
                actor_id=doc.get("actor_id"),
                department_id=doc.get("department_id"),
                correlation_id=doc.get("correlation_id"),
                idempotency_key=doc.get("idempotency_key"),
                payload=doc.get("payload") or {},
            )
            try:
                await self._event_bus.publish(event)
                replayed += 1
            except Exception:
                logger.exception("Replay failed for %s", event_id)
        return replayed
