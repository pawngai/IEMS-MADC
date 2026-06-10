from __future__ import annotations

from contexts.leave.contracts.ports import LeaveGateway


class LeaveQueryService:
    def __init__(self, *, gateway: LeaveGateway) -> None:
        self._gateway = gateway

    async def get_leave_balances(self, employee_id: str, *, current_user: dict) -> dict:
        return await self._gateway.get_leave_balances(employee_id, current_user=current_user)

    async def list_my_leaves(self, *, current_user: dict) -> list[dict]:
        return await self._gateway.list_my_leaves(current_user=current_user)

    async def list_leaves(
        self,
        *,
        status: str | None,
        leave_type_code: str | None,
        employee_id: str | None,
        current_user: dict,
    ) -> list[dict]:
        return await self._gateway.list_leaves(
            status=status,
            leave_type_code=leave_type_code,
            employee_id=employee_id,
            current_user=current_user,
        )
