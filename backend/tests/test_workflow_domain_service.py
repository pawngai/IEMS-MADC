from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.workflow.services import workflow_service as service


@pytest.mark.asyncio
async def test_transition_workflow_state_rejects_unsupported_action() -> None:
    with pytest.raises(HTTPException) as exc:
        await service.transitionWorkflowState(
            db=object(),
            task_id="TASK-1",
            action="UNKNOWN",
            actor_id="user-1",
            current_user={"sub": "user-1"},
        )

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_submit_approve_reject_delegate_to_transition(monkeypatch) -> None:
    calls: list[str] = []

    async def _fake_transition(**kwargs):
        calls.append(kwargs["action"])
        return {"ok": True, "action": kwargs["action"]}

    monkeypatch.setattr(service, "transitionWorkflowState", _fake_transition)

    await service.submitWorkflowAction(
        db=object(),
        task_id="TASK-1",
        actor_id="user-1",
        current_user={},
    )
    await service.approveWorkflowItem(
        db=object(),
        task_id="TASK-2",
        actor_id="user-1",
        current_user={},
    )
    await service.rejectWorkflowItem(
        db=object(),
        task_id="TASK-3",
        actor_id="user-1",
        current_user={},
    )

    assert calls == ["START_REVIEW", "COMPLETE", "REJECT"]
