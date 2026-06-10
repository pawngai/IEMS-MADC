from __future__ import annotations

from fastapi import HTTPException

from contexts.workflow.application.commands.task_commands import (
    AssignApprovalTask,
    CreateApprovalTask,
    TransitionApprovalTask,
)
from contexts.workflow.application.ports import (
    WorkflowAssigneeResolverGateway,
    WorkflowTaskRepositoryGateway,
)
from contexts.workflow.application.queries.task_queries import InboxQuery, OutboxQuery
from contexts.workflow.domain.aggregate import ApprovalTaskStatus, InvalidWorkflowTransition, WorkflowAggregate


class WorkflowTaskService:
    def __init__(
        self,
        *,
        repository: WorkflowTaskRepositoryGateway,
        assignee_resolver: WorkflowAssigneeResolverGateway,
    ) -> None:
        self._repository = repository
        self._assignee_resolver = assignee_resolver

    async def create_task(self, command: CreateApprovalTask) -> dict:
        assignee_user_id, assignee_role = await self._assignee_resolver.resolve_assignee(
            subject_type=command.subject_type,
            subject_id=command.subject_id,
            transition_name=command.transition_name,
            current_user=command.current_user,
            assignee_user_id=command.assignee_user_id,
            assignee_role=command.assignee_role,
        )

        task = await self._repository.create_task(
            subject_type=command.subject_type,
            subject_id=command.subject_id,
            transition_name=command.transition_name,
            from_state=command.from_state,
            to_state=command.to_state,
            requested_by=command.requested_by,
            assignee_user_id=assignee_user_id,
            assignee_role=assignee_role,
            payload=command.payload,
        )
        return task

    async def assign_task(self, command: AssignApprovalTask) -> dict:
        task = await self._repository.get_task(task_id=command.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        aggregate = WorkflowAggregate(
            current_state=ApprovalTaskStatus(str(task.get("status") or ApprovalTaskStatus.QUEUED.value))
        )
        try:
            new_state = aggregate.assign()
        except InvalidWorkflowTransition as exc:
            raise HTTPException(status_code=400, detail=exc.message) from exc

        assignee_user_id, assignee_role = await self._assignee_resolver.resolve_assignee(
            subject_type=str(task.get("subject_type") or ""),
            subject_id=str(task.get("subject_id") or ""),
            transition_name=str(task.get("transition_name") or ""),
            current_user=command.current_user,
            assignee_user_id=command.assignee_user_id,
            assignee_role=command.assignee_role,
        )

        updated = await self._repository.update_task(
            task_id=command.task_id,
            status=new_state.value,
            assignee_user_id=assignee_user_id,
            assignee_role=assignee_role,
            remarks=command.remarks,
            actor_id=command.actor_id,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found")

        await self._repository.append_transition(
            task_id=command.task_id,
            action="ASSIGN",
            from_status=str(task.get("status") or ApprovalTaskStatus.QUEUED.value),
            to_status=new_state.value,
            actor_id=command.actor_id,
            remarks=command.remarks,
        )
        return updated

    async def transition_task(self, command: TransitionApprovalTask) -> dict:
        task = await self._repository.get_task(task_id=command.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        aggregate = WorkflowAggregate(
            current_state=ApprovalTaskStatus(str(task.get("status") or ApprovalTaskStatus.QUEUED.value))
        )
        action_upper = command.action.upper()
        try:
            if action_upper == "START_REVIEW":
                new_state = aggregate.start_review()
            elif action_upper == "COMPLETE":
                new_state = aggregate.complete()
            elif action_upper == "REJECT":
                new_state = aggregate.reject()
            elif action_upper == "CANCEL":
                new_state = aggregate.cancel()
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported task action: {command.action}")
        except InvalidWorkflowTransition as exc:
            raise HTTPException(status_code=400, detail=exc.message) from exc

        updated = await self._repository.update_task(
            task_id=command.task_id,
            status=new_state.value,
            assignee_user_id=task.get("assignee_user_id"),
            assignee_role=task.get("assignee_role"),
            remarks=command.remarks,
            actor_id=command.actor_id,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found")

        await self._repository.append_transition(
            task_id=command.task_id,
            action=action_upper,
            from_status=str(task.get("status") or ApprovalTaskStatus.QUEUED.value),
            to_status=new_state.value,
            actor_id=command.actor_id,
            remarks=command.remarks,
        )
        return updated

    async def list_inbox(self, query: InboxQuery) -> list[dict]:
        return await self._repository.list_inbox(
            assignee_user_id=query.assignee_user_id,
            statuses=query.statuses,
            limit=query.limit,
        )

    async def list_outbox(self, query: OutboxQuery) -> list[dict]:
        return await self._repository.list_outbox(
            requested_by=query.requested_by,
            statuses=query.statuses,
            limit=query.limit,
        )

    async def get_task_transitions(self, *, task_id: str, limit: int = 200) -> list[dict]:
        return await self._repository.list_task_transitions(task_id=task_id, limit=limit)

    async def list_pending_by_target_state(self, *, to_state: str, limit: int = 200) -> list[dict]:
        return await self._repository.list_pending_by_target_state(
            to_state=to_state,
            limit=limit,
        )
