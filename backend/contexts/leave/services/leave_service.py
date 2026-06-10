from __future__ import annotations

from contexts.leave.contracts.dto import LeaveActionDTO, LeaveApplicationCreateDTO


async def applyLeaveRequest(*, service, payload: LeaveApplicationCreateDTO, current_user: dict) -> dict:
    return await service.apply_leave(payload, current_user=current_user)


async def approveLeave(*, service, leave_id: str, action: LeaveActionDTO, current_user: dict) -> dict:
    # Leave context remains owner of leave records and balances; approval is an operational transition.
    return await service.sanction_leave(leave_id, action, current_user=current_user)


async def updateLeaveBalance(*, service, employee_id: str, current_user: dict) -> dict:
    # Canonical balance refresh delegates to leave-owned balance computation/query path.
    return await service.get_leave_balances(employee_id, current_user=current_user)
