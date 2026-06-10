from __future__ import annotations

from typing import Protocol


class WorkflowTaskRepositoryGateway(Protocol):
    async def create_task(
        self,
        *,
        subject_type: str,
        subject_id: str,
        transition_name: str,
        from_state: str | None,
        to_state: str | None,
        requested_by: str,
        assignee_user_id: str | None,
        assignee_role: str | None,
        payload: dict | None,
    ) -> dict: ...

    async def get_task(self, *, task_id: str) -> dict | None: ...

    async def update_task(
        self,
        *,
        task_id: str,
        status: str,
        assignee_user_id: str | None,
        assignee_role: str | None,
        remarks: str | None,
        actor_id: str,
    ) -> dict | None: ...

    async def append_transition(
        self,
        *,
        task_id: str,
        action: str,
        from_status: str,
        to_status: str,
        actor_id: str,
        remarks: str | None,
    ) -> str: ...

    async def list_inbox(
        self,
        *,
        assignee_user_id: str,
        statuses: list[str] | None,
        limit: int,
    ) -> list[dict]: ...

    async def list_outbox(
        self,
        *,
        requested_by: str,
        statuses: list[str] | None,
        limit: int,
    ) -> list[dict]: ...

    async def list_task_transitions(self, *, task_id: str, limit: int) -> list[dict]: ...

    async def list_pending_by_target_state(
        self,
        *,
        to_state: str,
        limit: int,
    ) -> list[dict]: ...


class WorkflowAssigneeResolverGateway(Protocol):
    async def resolve_assignee(
        self,
        *,
        subject_type: str,
        subject_id: str,
        transition_name: str,
        current_user: dict,
        assignee_user_id: str | None,
        assignee_role: str | None,
    ) -> tuple[str | None, str | None]: ...
