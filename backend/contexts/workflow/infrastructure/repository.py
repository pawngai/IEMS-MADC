from __future__ import annotations

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from shared_kernel.ids import new_id
from shared_kernel.events import utc_now_iso


class WorkflowRepository:
    def __init__(self, *, db) -> None:
        self._db = db
        assert_collection_ownership(
            context="workflow", collection_name="workflow_tasks", write=True,
        )
        assert_collection_ownership(
            context="workflow", collection_name="workflow_transitions", write=True,
        )

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
    ) -> dict:
        task_id = new_id()
        now = utc_now_iso()
        document = {
            "task_id": task_id,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "transition_name": transition_name,
            "from_state": from_state,
            "to_state": to_state,
            "requested_by": requested_by,
            "assignee_user_id": assignee_user_id,
            "assignee_role": assignee_role,
            "payload": payload or {},
            "status": "QUEUED",
            "remarks": None,
            "created_at": now,
            "updated_at": now,
            "closed_at": None,
            "closed_by": None,
        }
        await self._db.workflow_tasks.insert_one(document)
        return document

    async def get_task(self, *, task_id: str) -> dict | None:
        return await self._db.workflow_tasks.find_one({"task_id": task_id}, {"_id": 0})

    async def update_task(
        self,
        *,
        task_id: str,
        status: str,
        assignee_user_id: str | None,
        assignee_role: str | None,
        remarks: str | None,
        actor_id: str,
    ) -> dict | None:
        closed_states = {"COMPLETED", "REJECTED", "CANCELLED"}
        now = utc_now_iso()
        set_fields = {
            "status": status,
            "assignee_user_id": assignee_user_id,
            "assignee_role": assignee_role,
            "remarks": remarks,
            "updated_at": now,
            "updated_by": actor_id,
        }
        if status in closed_states:
            set_fields["closed_at"] = now
            set_fields["closed_by"] = actor_id
        await self._db.workflow_tasks.update_one({"task_id": task_id}, {"$set": set_fields})
        return await self.get_task(task_id=task_id)

    async def append_transition(
        self,
        *,
        task_id: str,
        action: str,
        from_status: str,
        to_status: str,
        actor_id: str,
        remarks: str | None,
    ) -> str:
        transition_id = new_id()
        await self._db.workflow_transitions.insert_one(
            {
                "transition_id": transition_id,
                "task_id": task_id,
                "action": action,
                "from_status": from_status,
                "to_status": to_status,
                "actor_id": actor_id,
                "remarks": remarks,
                "created_at": utc_now_iso(),
            }
        )
        return transition_id

    async def list_inbox(
        self,
        *,
        assignee_user_id: str,
        statuses: list[str] | None,
        limit: int,
    ) -> list[dict]:
        query: dict = {"assignee_user_id": assignee_user_id}
        if statuses:
            query["status"] = {"$in": statuses}
        return (
            await self._db.workflow_tasks.find(query, {"_id": 0})
            .sort("updated_at", -1)
            .to_list(length=limit)
        )

    async def list_outbox(
        self,
        *,
        requested_by: str,
        statuses: list[str] | None,
        limit: int,
    ) -> list[dict]:
        query: dict = {"requested_by": requested_by}
        if statuses:
            query["status"] = {"$in": statuses}
        return (
            await self._db.workflow_tasks.find(query, {"_id": 0})
            .sort("updated_at", -1)
            .to_list(length=limit)
        )

    async def list_task_transitions(self, *, task_id: str, limit: int) -> list[dict]:
        return (
            await self._db.workflow_transitions.find({"task_id": task_id}, {"_id": 0})
            .sort("created_at", -1)
            .to_list(length=limit)
        )

    async def list_pending_by_target_state(self, *, to_state: str, limit: int) -> list[dict]:
        return (
            await self._db.workflow_tasks.find(
                {
                    "to_state": str(to_state or "").upper(),
                    "status": {"$in": ["QUEUED", "ASSIGNED", "IN_REVIEW"]},
                },
                {"_id": 0},
            )
            .sort("updated_at", -1)
            .to_list(length=limit)
        )
