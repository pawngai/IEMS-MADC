from __future__ import annotations

import pytest

from contexts.reporting.queries.analytics_queries import AnalyticsQueryService


def _matches_query(row: dict, query: dict) -> bool:
    for key, expected in (query or {}).items():
        actual = row.get(key)
        if isinstance(expected, dict) and "$in" in expected:
            if actual not in expected["$in"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def _apply_projection(row: dict, projection: dict | None) -> dict:
    if not projection:
        return dict(row)
    return {
        key: row.get(key)
        for key, include in projection.items()
        if key != "_id" and include
    }


class _FakeCursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = list(rows)
        self._limit: int | None = None

    def sort(self, key: str, direction: int):
        reverse = direction == -1
        self._rows.sort(key=lambda row: (row.get(key) is None, row.get(key)), reverse=reverse)
        return self

    def limit(self, limit: int):
        self._limit = limit
        return self

    async def to_list(self, *, length: int):
        rows = self._rows[: self._limit] if self._limit is not None else list(self._rows)
        return rows[:length]


class _FakeCollection:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = list(rows)
        self.aggregate_calls: list[list[dict]] = []

    def find(self, query: dict | None = None, projection: dict | None = None):
        filtered = [
            _apply_projection(row, projection)
            for row in self._rows
            if _matches_query(row, query or {})
        ]
        return _FakeCursor(filtered)

    async def count_documents(self, query: dict | None = None):
        return len([row for row in self._rows if _matches_query(row, query or {})])

    def aggregate(self, pipeline: list[dict]):
        self.aggregate_calls.append(pipeline)
        if pipeline == [{"$unwind": "$events"}, {"$count": "total"}]:
            total = sum(len(row.get("events") or []) for row in self._rows)
            return _FakeCursor([{"total": total}] if total else [])
        return _FakeCursor([])


class _FakeDb:
    def __init__(
        self,
        *,
        identities: list[dict],
        profile_read_models: list[dict] | None = None,
        service_book_records: list[dict] | None = None,
    ) -> None:
        self.employee_identities = _FakeCollection(identities)
        self.employee_profile_read_models = _FakeCollection(profile_read_models or [])
        self.service_book_records = _FakeCollection(service_book_records or [])


@pytest.mark.asyncio
async def test_workforce_drilldown_returns_expanded_identity_and_profile_fields():
    db = _FakeDb(
        identities=[
            {
                "employee_id": "emp-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Alice Example",
                "date_of_birth": "1990-01-01",
                "date_of_initial_engagement": "2024-01-15",
                "current_department_id": "FIN",
                "current_designation_id": "LDC",
                "current_office_id": "HQ",
                "reporting_officer_id": "emp-9",
                "employment_type": "REG",
                "employee_status": "ACTIVE",
                "status_effective_date": "2024-02-01",
                "gender": "FEMALE",
                "created_at": "2024-01-15T10:00:00+00:00",
                "updated_at": "2024-02-01T12:00:00+00:00",
            }
        ],
        profile_read_models=[
            {
                "employee_id": "emp-1",
                "workflow_status": "APPROVED",
                "service": "MCS",
                "group": "GROUP_B",
                "marital_status": "MARRIED",
            }
        ],
    )

    result = await AnalyticsQueryService(db).get_drilldown(
        section="workforce",
        dimension="all",
        limit=50,
    )

    assert result["section"] == "workforce"
    assert result["total"] == 1
    assert result["rows"] == [
        {
            "employee_id": "emp-1",
            "employee_code": "MADC-2024-R0001",
            "employee_name": "Alice Example",
            "date_of_birth": "1990-01-01",
            "date_of_initial_engagement": "2024-01-15",
            "department_id": "FIN",
            "designation_id": "LDC",
            "office_id": "HQ",
            "reporting_officer_id": "emp-9",
            "employment_type": "REG",
            "employee_status": "ACTIVE",
            "status_effective_date": "2024-02-01",
            "gender": "FEMALE",
            "workflow_status": "APPROVED",
            "service": "MCS",
            "service_group": "GROUP_B",
            "marital_status": "MARRIED",
            "created_at": "2024-01-15T10:00:00+00:00",
            "updated_at": "2024-02-01T12:00:00+00:00",
        }
    ]


@pytest.mark.asyncio
async def test_service_event_analytics_prefers_normalized_records_when_available():
    db = _FakeDb(
        identities=[],
        service_book_records=[{"service_event_id": "SE-1", "event_type": "PROMOTION"}],
    )

    await AnalyticsQueryService(db).get_service_event_analytics()

    assert len(db.service_book_records.aggregate_calls) == 3
    assert db.service_book_records.aggregate_calls[0] == [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]


@pytest.mark.asyncio
async def test_service_event_analytics_uses_normalized_records_when_empty():
    db = _FakeDb(
        identities=[],
        service_book_records=[],
    )

    await AnalyticsQueryService(db).get_service_event_analytics()

    assert len(db.service_book_records.aggregate_calls) == 3
    assert db.service_book_records.aggregate_calls[0] == [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]


@pytest.mark.asyncio
async def test_service_event_analytics_does_not_compare_legacy_streams():
    db = _FakeDb(
        identities=[],
        service_book_records=[{"service_event_id": "SE-1", "event_type": "PROMOTION"}],
    )

    await AnalyticsQueryService(db).get_service_event_analytics()

    assert len(db.service_book_records.aggregate_calls) == 3
    assert all("$unwind" not in stage for call in db.service_book_records.aggregate_calls for stage in call)


@pytest.mark.asyncio
async def test_service_event_drilldown_uses_normalized_match_and_projection():
    db = _FakeDb(
        identities=[],
        service_book_records=[{"service_event_id": "SE-1", "event_type": "PROMOTION"}],
    )

    await AnalyticsQueryService(db).get_drilldown(
        section="serviceEvents",
        dimension="type",
        value="PROMOTION",
    )

    rows_pipeline = db.service_book_records.aggregate_calls[0]
    count_pipeline = db.service_book_records.aggregate_calls[1]
    assert rows_pipeline[0] == {"$match": {"event_type": {"$in": ["PROMOTION"]}}}
    assert count_pipeline == [
        {"$match": {"event_type": {"$in": ["PROMOTION"]}}},
        {"$count": "total"},
    ]
    project_stage = next(stage["$project"] for stage in rows_pipeline if "$project" in stage)
    assert project_stage["service_event_id"] == 1
    assert project_stage["effective_date"] == "$effective_from"
