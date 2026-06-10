from __future__ import annotations

from fastapi import APIRouter, Depends

from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.rbac.domain.models import Permission
from contexts.service_book.opening.application.commands import (
    OpeningDocumentLink,
    OpeningRemarks,
    ServiceBookOpeningPayload,
)
from contexts.service_book.opening.application import opening_command_service
from contexts.service_book.opening.application import opening_query_service
from contexts.service_book.opening.application import opening_workflow_service


service_book_opening_router = APIRouter(prefix="/opening", tags=["Service Book Opening"])


@service_book_opening_router.get("")
async def list_service_book_openings(
    workflow_state: str | None = None,
    page_size: int = 200,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await opening_query_service.list_service_book_openings(
        db=db,
        workflow_state=workflow_state,
        page_size=page_size,
        current_user=current_user,
    )


@service_book_opening_router.get("/{employee_id}")
async def get_service_book_opening(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await opening_query_service.get_service_book_opening(
        db=db,
        employee_id=employee_id,
        current_user=current_user,
    )


@service_book_opening_router.get("/{employee_id}/part-i/defaults")
async def get_part_i_defaults(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await opening_query_service.get_part_i_defaults(
        db=db,
        employee_id=employee_id,
        current_user=current_user,
    )


@service_book_opening_router.post("")
async def create_service_book_opening_draft(
    payload: ServiceBookOpeningPayload,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await opening_command_service.upsert_draft(
        payload=payload,
        current_user=current_user,
        db=db,
        create=True,
    )


@service_book_opening_router.patch("/{employee_id}")
async def update_service_book_opening_draft(
    employee_id: str,
    payload: ServiceBookOpeningPayload,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    payload = payload.model_copy(update={"employee_id": employee_id})
    return await opening_command_service.upsert_draft(
        payload=payload,
        current_user=current_user,
        db=db,
        create=False,
    )


@service_book_opening_router.post("/{employee_id}/documents")
async def attach_service_book_opening_document(
    employee_id: str,
    payload: OpeningDocumentLink,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await opening_command_service.attach_document(
        db=db,
        employee_id=employee_id,
        payload=payload,
        current_user=current_user,
    )


async def _transition(
    *,
    employee_id: str,
    from_status: str,
    to_status: str,
    permission: Permission,
    timestamp_field: str,
    actor_field: str,
    remarks: OpeningRemarks,
    current_user: dict,
    db,
) -> dict:
    return await opening_workflow_service.transition(
        employee_id=employee_id,
        from_status=from_status,
        to_status=to_status,
        permission=permission,
        timestamp_field=timestamp_field,
        actor_field=actor_field,
        remarks=remarks,
        current_user=current_user,
        db=db,
    )


@service_book_opening_router.post("/{employee_id}/submit")
async def submit_service_book_opening(
    employee_id: str,
    remarks: OpeningRemarks,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _transition(
        employee_id=employee_id,
        from_status="DRAFT",
        to_status="SUBMITTED",
        permission=Permission.SERVICE_BOOK_OPENING_SUBMIT,
        timestamp_field="submitted_at",
        actor_field="submitted_by",
        remarks=remarks,
        current_user=current_user,
        db=db,
    )


@service_book_opening_router.post("/{employee_id}/verify")
async def verify_service_book_opening(
    employee_id: str,
    remarks: OpeningRemarks,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _transition(
        employee_id=employee_id,
        from_status="SUBMITTED",
        to_status="VERIFIED",
        permission=Permission.SERVICE_BOOK_OPENING_VERIFY,
        timestamp_field="verified_at",
        actor_field="verified_by",
        remarks=remarks,
        current_user=current_user,
        db=db,
    )


@service_book_opening_router.post("/{employee_id}/approve")
async def approve_service_book_opening(
    employee_id: str,
    remarks: OpeningRemarks,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _transition(
        employee_id=employee_id,
        from_status="VERIFIED",
        to_status="LOCKED",
        permission=Permission.SERVICE_BOOK_OPENING_APPROVE,
        timestamp_field="approved_at",
        actor_field="approved_by",
        remarks=remarks,
        current_user=current_user,
        db=db,
    )


__all__ = [
    "OpeningDocumentLink",
    "OpeningRemarks",
    "ServiceBookOpeningPayload",
    "service_book_opening_router",
]
