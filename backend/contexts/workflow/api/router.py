from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app_platform.db.runtime import get_db
from contexts.workflow.api.helpers import resolve_actor_id, validate_pending_stage_access
from contexts.workflow.application.commands.task_commands import (
    AssignApprovalTask,
    CreateApprovalTask,
)
from contexts.workflow.application.factory import build_workflow_service
from contexts.workflow.application.queries.task_queries import InboxQuery, OutboxQuery
from contexts.workflow.infrastructure.employee_gateway_adapter import (
    DefaultAssigneeResolverAdapter,
)
from contexts.workflow.infrastructure.repository import WorkflowRepository
from contexts.workflow.services.workflow_service import (
    _assert_workflow_payload_boundary,
    approveWorkflowItem,
    rejectWorkflowItem,
    submitWorkflowAction,
    transitionWorkflowState,
)
from app_platform.auth.current_user import get_current_user


workflow_router = APIRouter(prefix="/workflow", tags=["Workflow"])


def get_workflow_task_service(db=Depends(get_db)):
    repository = WorkflowRepository(db=db)
    resolver = DefaultAssigneeResolverAdapter()
    return build_workflow_service(repository=repository, assignee_resolver=resolver)


@workflow_router.post("/tasks")
async def create_task(
    body: dict,
    current_user: dict = Depends(get_current_user),
    service=Depends(get_workflow_task_service),
):
    requested_by = resolve_actor_id(current_user)
    payload = body.get("payload") or {}
    _assert_workflow_payload_boundary(payload)

    command = CreateApprovalTask(
        subject_type=str(body.get("subject_type") or ""),
        subject_id=str(body.get("subject_id") or ""),
        transition_name=str(body.get("transition_name") or ""),
        from_state=body.get("from_state"),
        to_state=body.get("to_state"),
        requested_by=requested_by,
        current_user=current_user,
        assignee_user_id=body.get("assignee_user_id"),
        assignee_role=body.get("assignee_role"),
        payload=payload,
    )
    if not command.subject_type or not command.subject_id or not command.transition_name:
        raise HTTPException(status_code=422, detail="subject_type, subject_id and transition_name are required")
    return await service.create_task(command)


@workflow_router.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    service=Depends(get_workflow_task_service),
):
    actor_id = resolve_actor_id(current_user)

    command = AssignApprovalTask(
        task_id=task_id,
        actor_id=actor_id,
        current_user=current_user,
        assignee_user_id=body.get("assignee_user_id"),
        assignee_role=body.get("assignee_role"),
        remarks=body.get("remarks"),
    )
    return await service.assign_task(command)


@workflow_router.post("/tasks/{task_id}/transition")
async def transition_task(
    task_id: str,
    body: dict,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = resolve_actor_id(current_user)

    action = str(body.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=422, detail="action is required")

    return await transitionWorkflowState(
        db=db,
        task_id=task_id,
        action=action,
        actor_id=actor_id,
        current_user=current_user,
        remarks=body.get("remarks"),
    )


@workflow_router.post("/tasks/{task_id}/submit")
async def submit_workflow_action(
    task_id: str,
    body: dict,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await submitWorkflowAction(
        db=db,
        task_id=task_id,
        actor_id=resolve_actor_id(current_user),
        current_user=current_user,
        remarks=body.get("remarks"),
    )


@workflow_router.post("/tasks/{task_id}/approve")
async def approve_workflow_item(
    task_id: str,
    body: dict,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await approveWorkflowItem(
        db=db,
        task_id=task_id,
        actor_id=resolve_actor_id(current_user),
        current_user=current_user,
        remarks=body.get("remarks"),
    )


@workflow_router.post("/tasks/{task_id}/reject")
async def reject_workflow_item(
    task_id: str,
    body: dict,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await rejectWorkflowItem(
        db=db,
        task_id=task_id,
        actor_id=resolve_actor_id(current_user),
        current_user=current_user,
        remarks=body.get("remarks"),
    )


@workflow_router.get("/inbox")
async def list_inbox(
    status: str | None = None,
    current_user: dict = Depends(get_current_user),
    service=Depends(get_workflow_task_service),
):
    assignee_user_id = resolve_actor_id(current_user)
    query = InboxQuery(
        assignee_user_id=assignee_user_id,
        statuses=[status] if status else None,
    )
    return await service.list_inbox(query)


@workflow_router.get("/outbox")
async def list_outbox(
    status: str | None = None,
    current_user: dict = Depends(get_current_user),
    service=Depends(get_workflow_task_service),
):
    requested_by = resolve_actor_id(current_user)
    query = OutboxQuery(
        requested_by=requested_by,
        statuses=[status] if status else None,
    )
    return await service.list_outbox(query)


@workflow_router.get("/tasks/{task_id}/transitions")
async def list_task_transitions(
    task_id: str,
    service=Depends(get_workflow_task_service),
):
    return await service.get_task_transitions(task_id=task_id)


@workflow_router.get("/pending/{stage}")
async def list_pending_stage(
    stage: str,
    current_user: dict = Depends(get_current_user),
    service=Depends(get_workflow_task_service),
):
    normalized_stage = validate_pending_stage_access(stage=stage, current_user=current_user)

    return await service.list_pending_by_target_state(to_state=normalized_stage)
