from __future__ import annotations

from contexts.workflow.application.ports import WorkflowAssigneeResolverGateway


class DefaultAssigneeResolverAdapter(WorkflowAssigneeResolverGateway):
    async def resolve_assignee(
        self,
        *,
        subject_type: str,
        subject_id: str,
        transition_name: str,
        current_user: dict,
        assignee_user_id: str | None,
        assignee_role: str | None,
    ) -> tuple[str | None, str | None]:
        _ = subject_type
        _ = subject_id
        _ = transition_name
        _ = current_user
        return assignee_user_id, assignee_role
