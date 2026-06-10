from __future__ import annotations

from typing import List, Optional

from app_platform.db.runtime import get_db
from contexts.leave.application.service import LeaveApplicationService
from contexts.leave.contracts.dto import (
    LeaveActionDTO,
    LeaveApplicationCreateDTO,
    LeaveApplicationResponseDTO,
)
from contexts.leave.infrastructure.gateway import LeaveMongoGateway
from contexts.rbac.policies.operational import require_leave_listing_permission
from contexts.leave.services.leave_service import (
    applyLeaveRequest,
    approveLeave,
    updateLeaveBalance,
)
from fastapi import APIRouter, Depends, Query, Request
from contexts.rbac.domain.models import Permission
from contexts.rbac.application.access_control import require_permissions
from app_platform.auth.current_user import get_current_user

leave_router = APIRouter(prefix="/leave", tags=["Leave Management"])


def get_leave_service(request: Request, db=Depends(get_db)) -> LeaveApplicationService:
    container = getattr(request.app.state, "container", None)
    outbox_repo = container.outbox_repo if container is not None else None
    leave_rules_evaluator = (
        container.leave_rules_evaluator if container is not None else None
    )
    gateway = LeaveMongoGateway(db)
    return LeaveApplicationService(
        gateway=gateway,
        outbox_repo=outbox_repo,
        leave_rules_evaluator=leave_rules_evaluator,
    )


@leave_router.get("/balances/{employee_id}")
async def get_leave_balances(
    employee_id: str,
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    if (current_user.get("employee_id") or "") == employee_id:
        require_permissions(current_user, Permission.LEAVE_READ_OWN)
    else:
        require_permissions(current_user, Permission.LEAVE_READ_ALL)
    return await updateLeaveBalance(
        service=service,
        employee_id=employee_id,
        current_user=current_user,
    )


@leave_router.post("/apply", response_model=LeaveApplicationResponseDTO)
async def apply_leave(
    payload: LeaveApplicationCreateDTO,
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.LEAVE_APPLY_OWN)
    return await applyLeaveRequest(
        service=service,
        payload=payload,
        current_user=current_user,
    )


@leave_router.get("/my", response_model=List[LeaveApplicationResponseDTO])
async def list_my_leaves(
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.LEAVE_READ_OWN)
    return await service.list_my_leaves(current_user=current_user)


@leave_router.get("/", response_model=List[LeaveApplicationResponseDTO])
async def list_leaves(
    status: Optional[str] = Query(default=None),
    leave_type_code: Optional[str] = Query(default=None),
    employee_id: Optional[str] = Query(default=None),
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    require_leave_listing_permission(current_user)
    return await service.list_leaves(
        status=status,
        leave_type_code=leave_type_code,
        employee_id=employee_id,
        current_user=current_user,
    )


@leave_router.post("/{leave_id}/recommend", response_model=LeaveApplicationResponseDTO)
async def recommend_leave(
    leave_id: str,
    action: LeaveActionDTO,
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.LEAVE_RECOMMEND)
    return await service.recommend_leave(leave_id, action, current_user=current_user)


@leave_router.post("/{leave_id}/sanction", response_model=LeaveApplicationResponseDTO)
async def sanction_leave(
    leave_id: str,
    action: LeaveActionDTO,
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    # Permission check is deferred to the service layer (CL can be sanctioned
    # directly by HOD with LEAVE_RECOMMEND).
    return await approveLeave(
        service=service,
        leave_id=leave_id,
        action=action,
        current_user=current_user,
    )


@leave_router.post("/{leave_id}/reject", response_model=LeaveApplicationResponseDTO)
async def reject_leave(
    leave_id: str,
    action: LeaveActionDTO,
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(
        current_user, Permission.LEAVE_RECOMMEND, Permission.LEAVE_SANCTION
    )
    return await service.reject_leave(leave_id, action, current_user=current_user)


@leave_router.post("/{leave_id}/cancel", response_model=LeaveApplicationResponseDTO)
async def cancel_leave(
    leave_id: str,
    action: LeaveActionDTO,
    service: LeaveApplicationService = Depends(get_leave_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.LEAVE_APPLY_OWN)
    return await service.cancel_leave(leave_id, action, current_user=current_user)
