from __future__ import annotations

from typing import Any

from contexts.workflow.application.commands.task_commands import TransitionApprovalTask
from contexts.workflow.application.factory import build_workflow_service
from contexts.workflow.infrastructure.employee_gateway_adapter import (
    DefaultAssigneeResolverAdapter,
)
from contexts.workflow.infrastructure.repository import WorkflowRepository
from fastapi import HTTPException


WORKFLOW_ACTION_SUBMIT = "START_REVIEW"
WORKFLOW_ACTION_APPROVE = "COMPLETE"
WORKFLOW_ACTION_REJECT = "REJECT"


_ALLOWED_WORKFLOW_ACTIONS = {
    WORKFLOW_ACTION_SUBMIT,
    WORKFLOW_ACTION_APPROVE,
    WORKFLOW_ACTION_REJECT,
    "CANCEL",
}


_WORKFLOW_ONLY_FIELDS = {
    "workflow_status",
    "workflow_state",
    "workflow_stage",
    "workflow_queue",
    "task_state",
    "decision",
    "remarks",
}


def _build_workflow_task_service(*, db):
    repository = WorkflowRepository(db=db)
    resolver = DefaultAssigneeResolverAdapter()
    return build_workflow_service(repository=repository, assignee_resolver=resolver)


def _assert_workflow_payload_boundary(payload: dict[str, Any] | None) -> None:
    if not payload:
        return

    for key in payload.keys():
        normalized = str(key or "").strip().lower()
        if normalized.startswith("employee_") or normalized.startswith("service_book"):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Workflow payload must remain process metadata only and cannot "
                    "become employee or service-history business truth"
                ),
            )

    if not any(str(key or "").strip().lower() in _WORKFLOW_ONLY_FIELDS for key in payload.keys()):
        raise HTTPException(
            status_code=422,
            detail=(
                "Workflow payload must include workflow process metadata; "
                "business-domain truth must stay in owning contexts"
            ),
        )


async def transitionWorkflowState(
    *,
    db,
    task_id: str,
    action: str,
    actor_id: str,
    current_user: dict,
    remarks: str | None = None,
) -> dict[str, Any]:
    action_upper = str(action or "").strip().upper()
    if action_upper not in _ALLOWED_WORKFLOW_ACTIONS:
        raise HTTPException(status_code=422, detail=f"Unsupported workflow action: {action}")

    service = _build_workflow_task_service(db=db)
    result = await service.transition_task(
        TransitionApprovalTask(
            task_id=task_id,
            action=action_upper,
            actor_id=actor_id,
            current_user=current_user,
            remarks=remarks,
        )
    )
    return result


async def submitWorkflowAction(
    *,
    db,
    task_id: str,
    actor_id: str,
    current_user: dict,
    remarks: str | None = None,
) -> dict[str, Any]:
    return await transitionWorkflowState(
        db=db,
        task_id=task_id,
        action=WORKFLOW_ACTION_SUBMIT,
        actor_id=actor_id,
        current_user=current_user,
        remarks=remarks,
    )


async def approveWorkflowItem(
    *,
    db,
    task_id: str,
    actor_id: str,
    current_user: dict,
    remarks: str | None = None,
) -> dict[str, Any]:
    return await transitionWorkflowState(
        db=db,
        task_id=task_id,
        action=WORKFLOW_ACTION_APPROVE,
        actor_id=actor_id,
        current_user=current_user,
        remarks=remarks,
    )


async def rejectWorkflowItem(
    *,
    db,
    task_id: str,
    actor_id: str,
    current_user: dict,
    remarks: str | None = None,
) -> dict[str, Any]:
    return await transitionWorkflowState(
        db=db,
        task_id=task_id,
        action=WORKFLOW_ACTION_REJECT,
        actor_id=actor_id,
        current_user=current_user,
        remarks=remarks,
    )
