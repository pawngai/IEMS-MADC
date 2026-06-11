from __future__ import annotations

import pytest

from contexts.identity_access.rbac.domain.models import Authority
from contexts.service_book.records.api import router as service_events_router


class _FakeCollection:
    def __init__(self, document=None) -> None:
        self._document = document

    async def find_one(self, query, projection=None):
        return self._document


class _FakeDb:
    def __init__(self, summary=None) -> None:
        self._summary = summary

    def __getitem__(self, name: str):
        assert name == "employee_service_summaries"
        return _FakeCollection(self._summary)


@pytest.mark.asyncio
async def test_existing_employee_without_service_summary_returns_null(monkeypatch) -> None:
    async def fake_resolve_identity_ref(db, *, ref: str):
        assert ref == "EMP-1"
        return {"employee_id": "EMP-1"}

    monkeypatch.setattr(service_events_router, "resolve_identity_ref", fake_resolve_identity_ref)

    response = await service_events_router.get_employee_service_summary(
        employee_id="EMP-1",
        current_user={"authorities": [Authority.GLOBAL_DATA_ENTRY.value]},
        db=_FakeDb(summary=None),
    )

    assert response is None