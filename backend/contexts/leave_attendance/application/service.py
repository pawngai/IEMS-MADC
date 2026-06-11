from __future__ import annotations

from collections.abc import Callable
from app_platform.outbox.repo import OutboxRepository
from contexts.leave_attendance.application.command_service import LeaveCommandService
from contexts.leave_attendance.application.eventing import LeaveEventPublisher
from contexts.leave_attendance.application.query_service import LeaveQueryService
from contexts.leave_attendance.contracts.dto import LeaveActionDTO, LeaveApplicationCreateDTO
from contexts.leave_attendance.contracts.ports import LeaveGateway


class LeaveApplicationService:
    def __init__(
        self,
        *,
        gateway: LeaveGateway,
        outbox_repo: OutboxRepository | None,
        leave_rules_evaluator: Callable[[dict], dict] | None = None,
    ) -> None:
        event_publisher = LeaveEventPublisher(outbox_repo=outbox_repo)
        self._queries = LeaveQueryService(gateway=gateway)
        self._commands = LeaveCommandService(
            gateway=gateway,
            event_publisher=event_publisher,
            leave_rules_evaluator=leave_rules_evaluator,
        )

    async def get_leave_balances(self, employee_id: str, *, current_user: dict) -> dict:
        return await self._queries.get_leave_balances(employee_id, current_user=current_user)

    async def list_my_leaves(self, *, current_user: dict) -> list[dict]:
        return await self._queries.list_my_leaves(current_user=current_user)

    async def list_leaves(
        self,
        *,
        status: str | None,
        leave_type_code: str | None,
        employee_id: str | None,
        current_user: dict,
    ) -> list[dict]:
        return await self._queries.list_leaves(
            status=status,
            leave_type_code=leave_type_code,
            employee_id=employee_id,
            current_user=current_user,
        )

    async def apply_leave(self, payload: LeaveApplicationCreateDTO, *, current_user: dict) -> dict:
        return await self._commands.apply_leave(payload, current_user=current_user)

    async def recommend_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        return await self._commands.recommend_leave(
            leave_id, action, current_user=current_user
        )

    async def sanction_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        return await self._commands.sanction_leave(
            leave_id, action, current_user=current_user
        )

    async def reject_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        return await self._commands.reject_leave(
            leave_id, action, current_user=current_user
        )

    async def cancel_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        return await self._commands.cancel_leave(
            leave_id, action, current_user=current_user
        )
