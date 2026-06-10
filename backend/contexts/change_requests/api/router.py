from __future__ import annotations

from typing import Optional

from app_platform.db.runtime import get_db
from contexts.change_requests.application.service import ChangeRequestApplicationService
from contexts.change_requests.contracts.dto import (
    CreateChangeRequestDTO,
    ReviewChangeRequestDTO,
)
from contexts.change_requests.infrastructure.gateway import ChangeRequestMongoGateway
from fastapi import APIRouter, Depends, Query, Request
from contexts.identity_access.contracts.models import Permission
from contexts.identity_access.contracts.access_control import require_permissions
from app_platform.auth.current_user import get_current_user

change_request_ess_router = APIRouter(
    prefix="/ess/change-requests", tags=["ESS – Change Requests"]
)
change_request_admin_router = APIRouter(
    prefix="/change-requests", tags=["Change Requests (Admin)"]
)


def get_change_request_service(
    request: Request, db=Depends(get_db)
) -> ChangeRequestApplicationService:
    container = getattr(request.app.state, "container", None)
    outbox_repo = container.outbox_repo if container is not None else None
    gateway = ChangeRequestMongoGateway(db)
    return ChangeRequestApplicationService(gateway=gateway, outbox_repo=outbox_repo)


@change_request_ess_router.post("")
async def submit_change_request(
    payload: CreateChangeRequestDTO,
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(
        current_user, Permission.PROFILE_READ_OWN, Permission.PROFILE_UPDATE_OWN_LIMITED
    )
    return await service.create_change_request(payload, current_user=current_user)


@change_request_ess_router.get("")
async def list_my_change_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(
        current_user, Permission.PROFILE_READ_OWN, Permission.PROFILE_UPDATE_OWN_LIMITED
    )
    return await service.list_my_change_requests(
        current_user=current_user, status=status
    )


@change_request_ess_router.get("/{request_id}")
async def get_my_change_request(
    request_id: str,
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(
        current_user, Permission.PROFILE_READ_OWN, Permission.PROFILE_UPDATE_OWN_LIMITED
    )
    return await service.get_change_request(request_id, current_user=current_user)


@change_request_ess_router.post("/{request_id}/cancel")
async def cancel_my_change_request(
    request_id: str,
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(
        current_user, Permission.PROFILE_READ_OWN, Permission.PROFILE_UPDATE_OWN_LIMITED
    )
    return await service.cancel_change_request(request_id, current_user=current_user)


@change_request_admin_router.get("/pending-count")
async def get_pending_count(
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.PROFILE_READ_ALL)
    count = await service.get_pending_count(current_user=current_user)
    return {"pending_count": count}


@change_request_admin_router.get("")
async def list_change_requests(
    status: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.PROFILE_READ_ALL)
    return await service.list_change_requests(
        current_user=current_user,
        status=status,
        employee_id=employee_id,
        page=page,
        page_size=page_size,
    )


@change_request_admin_router.get("/{request_id}")
async def get_change_request(
    request_id: str,
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.PROFILE_READ_ALL)
    return await service.get_change_request(request_id, current_user=current_user)


@change_request_admin_router.post("/{request_id}/review")
async def review_change_request(
    request_id: str,
    payload: ReviewChangeRequestDTO,
    service: ChangeRequestApplicationService = Depends(get_change_request_service),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.PROFILE_UPDATE_ALL)
    return await service.review_change_request(
        request_id,
        action=payload.action,
        remarks=payload.remarks,
        current_user=current_user,
    )
