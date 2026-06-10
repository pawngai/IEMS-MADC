from __future__ import annotations

from contexts.workflow.application.ports import (
    WorkflowAssigneeResolverGateway,
    WorkflowTaskRepositoryGateway,
)
from contexts.workflow.application.services.task_service import WorkflowTaskService


def build_workflow_service(
    *,
    repository: WorkflowTaskRepositoryGateway,
    assignee_resolver: WorkflowAssigneeResolverGateway,
) -> WorkflowTaskService:
    return WorkflowTaskService(repository=repository, assignee_resolver=assignee_resolver)
