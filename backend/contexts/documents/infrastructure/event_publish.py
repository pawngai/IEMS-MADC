"""Documents infrastructure — outbox event publishing."""
from __future__ import annotations

from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository


async def publish_document_event(
	*,
	name: str,
	payload: dict,
	db=None,
	actor_id: str | None = None,
	department_id: str | None = None,
	session=None,
) -> None:
	if db is None:
		return
	await OutboxRepository(db).add_event(
		OutboxEvent(
			name=name,
			payload=payload,
			actor_id=actor_id,
			department_id=department_id,
		),
		session=session,
	)
