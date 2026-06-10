from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from contexts.identity_access.contracts.access_control import require_owner_or_permissions
from contexts.identity_access.contracts.models import Permission
from contexts.service_book.application.queries import get_opening_part_i_defaults
from contexts.service_book.opening.application.commands import OpeningDocumentLink, ServiceBookOpeningPayload
from contexts.service_book.opening.application.opening_query_service import resolve_identity_or_404
from contexts.service_book.opening.domain.opening import normalize_parts, opening_response
from contexts.service_book.opening.domain.opening_policy import require_regular_opening
from contexts.service_book.opening.domain.opening_status import EDITABLE_STATUSES, normalize_status
from contexts.service_book.opening.infrastructure.opening_repository import find_opening, save_opening


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def actor_id(current_user: dict) -> str:
    return str(current_user.get("sub") or current_user.get("id") or current_user.get("email") or "system")


async def upsert_draft(
    *,
    payload: ServiceBookOpeningPayload,
    current_user: dict,
    db,
    create: bool,
) -> dict:
    identity = await resolve_identity_or_404(db, payload.employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(
        current_user,
        resolved_id,
        Permission.SERVICE_BOOK_OPENING_CREATE if create else Permission.SERVICE_BOOK_OPENING_UPDATE,
    )
    require_regular_opening(identity)
    existing = await find_opening(db, resolved_id)
    existing_status = normalize_status((existing or {}).get("status"))
    if existing_status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Submitted Service Book Opening cannot be edited")

    parts = normalize_parts(payload.parts)
    parts["part_i"] = {
        **await get_opening_part_i_defaults(db, employee_ref=resolved_id, identity=identity),
        **parts.get("part_i", {}),
        "employee_id": resolved_id,
    }
    now = now_iso()
    document = {
        **(existing or {}),
        "id": (existing or {}).get("id") or f"SBO-{resolved_id}",
        "opening_id": (existing or {}).get("opening_id") or f"SBO-{resolved_id}",
        "employee_id": resolved_id,
        "employee_code": identity.get("employee_code"),
        "full_name": identity.get("full_name") or identity.get("name_in_block_letters"),
        "status": "DRAFT",
        "workflow_status": "DRAFT",
        "parts": parts,
        "documents": list(payload.documents or (existing or {}).get("documents") or []),
        "updated_at": now,
        "updated_by": actor_id(current_user),
    }
    saved = await save_opening(db, document)
    return opening_response(saved, employee_id=resolved_id, identity=identity)


async def attach_document(*, db, employee_id: str, payload: OpeningDocumentLink, current_user: dict) -> dict:
    identity = await resolve_identity_or_404(db, employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(current_user, resolved_id, Permission.SERVICE_BOOK_OPENING_UPDATE)
    require_regular_opening(identity)
    opening = await find_opening(db, resolved_id)
    if not opening:
        await upsert_draft(
            payload=ServiceBookOpeningPayload(employee_id=resolved_id, parts={}, documents=[]),
            current_user=current_user,
            db=db,
            create=True,
        )
    current = await find_opening(db, resolved_id) or opening or {}
    documents = list(current.get("documents") or [])
    doc = {
        "document_id": payload.document_id,
        "document_type": payload.document_type or "opening",
        "name": payload.name or payload.document_id,
        "attached_at": now_iso(),
        "attached_by": actor_id(current_user),
    }
    if payload.field_key:
        doc["field_key"] = payload.field_key
    if payload.field_label:
        doc["field_label"] = payload.field_label
    if payload.part_id:
        doc["part_id"] = payload.part_id
    if not any(item.get("document_id") == payload.document_id for item in documents):
        documents.append(doc)
    current["documents"] = documents
    current["updated_at"] = now_iso()
    saved = await save_opening(db, current)
    return opening_response(saved, employee_id=resolved_id, identity=identity)
