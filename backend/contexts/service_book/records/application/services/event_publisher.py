from __future__ import annotations

from app_platform.db.atomic import call_with_optional_session
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository


class ServiceEventsEventPublisher:
    def __init__(self, *, outbox_repo: OutboxRepository | None) -> None:
        self._outbox_repo = outbox_repo

    async def publish(
        self,
        *,
        name: str,
        payload: dict,
        actor_id: str | None,
        session=None,
    ) -> None:
        if self._outbox_repo is None:
            return
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(name=name, payload=payload, actor_id=actor_id),
            session=session,
        )
