from __future__ import annotations

from fastapi import HTTPException

from contexts.rbac.application.authorization_service import canPerformAction
from contexts.rbac.application.access_control import has_active_authority, has_authority, require_permissions
from contexts.rbac.domain.models import Authority, Permission


_DOCUMENT_DELETE_AUTHORITIES = {
    Authority.SYSTEM_ADMIN.value,
    Authority.GLOBAL_DATA_ENTRY.value,
    Authority.DEALING_ASSISTANT.value,
    Authority.DEPT_DATA_ENTRY.value,
    Authority.APPROVING_AUTHORITY.value,
}


def _has_document_management_authority(current_user: dict) -> bool:
    return has_active_authority(current_user, *_DOCUMENT_DELETE_AUTHORITIES)


def require_document_delete_permission(current_user: dict) -> None:
    if _has_document_management_authority(current_user):
        return
    raise HTTPException(
        status_code=403,
        detail="Only administrators or data-entry officers may delete documents.",
    )


def can_manage_documents(current_user: dict) -> bool:
    return _has_document_management_authority(current_user)


_LEGAL_HOLD_AUTHORITIES = {Authority.SYSTEM_ADMIN.value}


def require_legal_hold_authority(current_user: dict) -> None:
    """Legal hold is reserved to system administrators — it bypasses retention
    and approval-lock semantics, so the surface is intentionally narrow."""
    if has_active_authority(current_user, *_LEGAL_HOLD_AUTHORITIES):
        return
    raise HTTPException(
        status_code=403,
        detail="Only system administrators may apply or release a legal hold on a document.",
    )


def can_read_pay(*, current_user: dict, employee_id: str) -> bool:
    if (current_user.get("employee_id") or "") == employee_id:
        return canPerformAction(
            current_user,
            required_permissions=[Permission.IDENTITY_READ_OWN.value],
            target_employee_id=employee_id,
        )
    return canPerformAction(
        current_user,
        required_permissions=[
            Permission.IDENTITY_READ_ALL.value,
            Permission.SERVICE_BOOK_READ_ALL.value,
            Permission.ESTABLISHMENT_PAY_FIXATION.value,
        ],
        target_employee_id=employee_id,
    )


def require_pay_write(current_user: dict) -> None:
    require_permissions(current_user, Permission.ESTABLISHMENT_PAY_FIXATION)


def require_leave_listing_permission(current_user: dict) -> None:
    require_permissions(
        current_user,
        Permission.LEAVE_READ_ALL,
        Permission.LEAVE_RECOMMEND,
        Permission.LEAVE_SANCTION,
    )
