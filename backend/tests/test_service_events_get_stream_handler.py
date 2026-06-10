from __future__ import annotations

import pytest

from contexts.service_book.records.application.handlers.get_stream_handler import GetStreamHandler
from contexts.service_book.records.application.queries.get_stream import GetServiceEventStreamQuery


class _FakeRepository:
    def __init__(self, stream_doc: dict | None) -> None:
        self._stream_doc = stream_doc

    async def get_stream(self, employee_id: str) -> dict | None:
        _ = employee_id
        return self._stream_doc


@pytest.mark.asyncio
async def test_get_stream_handler_returns_flattened_ui_aliases() -> None:
    handler = GetStreamHandler(
        repository=_FakeRepository(
            {
                "employee_id": "EMP-100",
                "events": [
                    {
                        "service_event_id": "SE-1",
                        "event_type": "PROMOTION",
                        "payload": {"to_post": "Senior Assistant"},
                        "date_range": {
                            "effective_from": "2026-03-15",
                            "effective_to": "2026-03-20",
                        },
                        "part_code": "IV",
                        "source_ref": {
                            "context": "workflow",
                            "reference_id": "WF-22",
                            "revision": 3,
                        },
                        "status": "APPROVED",
                        "is_voided": False,
                        "created_at": "2026-03-10T10:00:00Z",
                        "created_by": "actor-1",
                        "revisions": [
                            {
                                "revision": 1,
                                "reason": "Corrected order number",
                                "actor_id": "actor-2",
                                "payload": {"to_post": "Senior Assistant"},
                                "corrected_at": "2026-03-12T10:00:00Z",
                            }
                        ],
                    }
                ],
            }
        )
    )

    result = await handler.handle(query=GetServiceEventStreamQuery(employee_id="EMP-100"))

    assert result["employee_id"] == "EMP-100"
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["id"] == "SE-1"
    assert event["effective_from"] == "2026-03-15"
    assert event["effective_to"] == "2026-03-20"
    assert event["recorded_at"] == "2026-03-10T10:00:00Z"
    assert event["actor_id"] == "actor-1"
    assert event["source_context"] == "workflow"
    assert event["source_reference_id"] == "WF-22"
    assert event["source_revision"] == 3
    assert event["corrected"] is True
    assert event["correction_reason"] == "Corrected order number"
    assert event["date_range"] == {
        "effective_from": "2026-03-15",
        "effective_to": "2026-03-20",
    }


@pytest.mark.asyncio
async def test_get_stream_handler_returns_empty_stream_for_missing_document() -> None:
    handler = GetStreamHandler(repository=_FakeRepository(None))

    result = await handler.handle(query=GetServiceEventStreamQuery(employee_id="EMP-404"))

    assert result == {"employee_id": "EMP-404", "events": []}