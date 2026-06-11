from __future__ import annotations

from contexts.employee_master.profile.application.services.workflow_engine import (
    EmployeeWorkflowApplicationService,
)
from contexts.employee_master.profile.infrastructure.gateway import EmployeeWorkflowEventOutboxGateway
from contexts.employee_master.profile.repository.profile_read_repository import (
    EmployeeProfileReadMongoGateway,
)
from contexts.employee_master.profile.repository.profile_repository import (
    EmployeeProfileAuditMongoGateway,
    EmployeeProfileRepositoryMongoGateway,
    EmployeeProfileWorkflowMongoGateway,
)
from fastapi import Request


def build_employee_workflow_service(
    *,
    request: Request,
    db,
) -> EmployeeWorkflowApplicationService:
    container = getattr(request.app.state, "container", None)
    outbox_repo = container.outbox_repo if container is not None else None

    event_gateway = EmployeeWorkflowEventOutboxGateway(outbox_repo=outbox_repo)
    profile_gateway = EmployeeProfileWorkflowMongoGateway(db=db)
    profile_repo_gateway = EmployeeProfileRepositoryMongoGateway(db=db)
    profile_read_gateway = EmployeeProfileReadMongoGateway(db=db)
    audit_gateway = EmployeeProfileAuditMongoGateway(db=db)

    return EmployeeWorkflowApplicationService(
        gateway=event_gateway,
        profile_gateway=profile_gateway,
        profile_repo_gateway=profile_repo_gateway,
        profile_read_gateway=profile_read_gateway,
        audit_gateway=audit_gateway,
    )
