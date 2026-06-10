from __future__ import annotations

from fastapi import HTTPException

from contexts.rbac.application.access_control import require_owner_or_permissions, require_permissions
from contexts.rbac.domain.models import Permission
from contexts.service_book.application.queries import get_opening_part_i_defaults, resolve_employee_identity
from contexts.service_book.opening.domain.opening import opening_response
from contexts.service_book.opening.domain.opening_policy import require_regular_opening
from contexts.service_book.opening.domain.opening_status import normalize_status
from contexts.service_book.opening.infrastructure.opening_repository import find_opening, list_openings


async def resolve_identity_or_404(db, employee_ref: str) -> dict:
    identity = await resolve_employee_identity(db, employee_ref)
    if identity and str(identity.get("employee_id") or "").strip():
        return identity
    raise HTTPException(
        status_code=404,
        detail={"error_code": "EMPLOYEE_NOT_FOUND", "message": f"Employee '{employee_ref}' not found"},
    )


async def list_service_book_openings(*, db, workflow_state: str | None, page_size: int, current_user: dict) -> dict:
    require_permissions(current_user, Permission.SERVICE_BOOK_READ_ALL)
    query = {"status": normalize_status(workflow_state)} if workflow_state else {}
    rows = await list_openings(db, query=query, limit=page_size)
    return {"items": [opening_response(row, employee_id=str(row.get("employee_id") or "")) for row in rows]}


async def get_service_book_opening(*, db, employee_id: str, current_user: dict) -> dict:
    identity = await resolve_identity_or_404(db, employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(current_user, resolved_id, Permission.SERVICE_BOOK_READ_ALL)
    require_regular_opening(identity)
    opening = await find_opening(db, resolved_id)
    if not opening:
        return opening_response({"status": "NOT_STARTED"}, employee_id=resolved_id, identity=identity)
    return opening_response(opening, employee_id=resolved_id, identity=identity)


async def get_part_i_defaults(*, db, employee_id: str, current_user: dict) -> dict:
    identity = await resolve_identity_or_404(db, employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(current_user, resolved_id, Permission.SERVICE_BOOK_READ_ALL)
    require_regular_opening(identity)
    return {"part_i": await get_opening_part_i_defaults(db, employee_ref=resolved_id, identity=identity)}
