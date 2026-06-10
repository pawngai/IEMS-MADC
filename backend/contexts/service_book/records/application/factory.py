from __future__ import annotations

from contexts.service_book.records.application.service_summary_projection import (
    EmployeeServiceSummaryProjectionService,
)
from contexts.service_book.records.application.service import ServiceEventApplicationService
from contexts.service_book.records.repository.service_record_repository import ServiceRecordRepository
from contexts.service_book.records.repository.service_summary_repository import (
    EmployeeServiceSummaryRepository,
)


def build_service_event_application_service(*, db, outbox_repo=None) -> ServiceEventApplicationService:
    return ServiceEventApplicationService(
        repository=ServiceRecordRepository(db=db),
        outbox_repo=outbox_repo,
        service_summary_projection=EmployeeServiceSummaryProjectionService(
            repository=EmployeeServiceSummaryRepository(db=db),
        ),
    )
