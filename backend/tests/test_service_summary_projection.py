from __future__ import annotations

import pytest

from contexts.service_book.records.application.service_summary_projection import (
    EmployeeServiceSummaryProjectionService,
)


class _FakeSummaryRepository:
    def __init__(self, current: dict | None = None) -> None:
        self.current = current
        self.upserts: list[dict] = []

    async def get_summary(self, *, employee_id: str):
        assert employee_id == "EMP-1"
        return self.current

    async def upsert_summary(self, *, employee_id: str, summary: dict):
        assert employee_id == "EMP-1"
        self.upserts.append(summary)
        return {"employee_id": employee_id, **summary}


@pytest.mark.asyncio
async def test_rate_revision_projection_preserves_current_assignment_fields() -> None:
    repository = _FakeSummaryRepository(
        {
            "employee_id": "EMP-1",
            "current_department_id": "PWD",
            "current_office_id": "OFFICE-1",
            "current_designation_id": "WORKER",
            "current_service_id": "WORKS",
            "current_post_id": "POST-1",
            "current_employment_type_code": "WAGES",
            "current_employment_class": "NON_REGULAR",
            "current_service_status": "ENGAGED",
            "daily_wage_rate": 500,
        }
    )
    service = EmployeeServiceSummaryProjectionService(repository=repository)

    projected = await service.project_posted_record(
        service_record={
            "service_event_id": "SR-2",
            "employee_id": "EMP-1",
            "event_type": "WAGES_RATE_REVISED",
            "payload": {
                "record_type": "WAGES_RATE_REVISED",
                "employment_type_code": "WAGES",
                "daily_wage_rate": 550,
            },
        }
    )

    assert projected["current_department_id"] == "PWD"
    assert projected["current_office_id"] == "OFFICE-1"
    assert projected["current_designation_id"] == "WORKER"
    assert projected["current_service_id"] == "WORKS"
    assert projected["current_post_id"] == "POST-1"
    assert projected["current_service_status"] == "ENGAGED"
    assert projected["daily_wage_rate"] == 550
