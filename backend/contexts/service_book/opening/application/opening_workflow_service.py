from __future__ import annotations

import json

from fastapi import HTTPException

from contexts.rbac.application.access_control import require_permissions
from contexts.rbac.domain.models import Permission
from contexts.service_book.records.repository.service_summary_repository import EmployeeServiceSummaryRepository
from contexts.service_book.opening.application.commands import OpeningRemarks
from contexts.service_book.opening.application.opening_command_service import actor_id, now_iso
from contexts.service_book.opening.application.opening_query_service import resolve_identity_or_404
from contexts.service_book.opening.domain.opening import normalize_parts, opening_response
from contexts.service_book.opening.domain.opening_policy import require_regular_opening
from contexts.service_book.opening.domain.opening_status import normalize_status
from contexts.service_book.opening.domain.required_parts_policy import missing_required_parts
from contexts.service_book.opening.infrastructure.opening_repository import find_opening, save_opening


def _collection(db, name: str):
    collection = getattr(db, name, None)
    if collection is not None:
        return collection
    try:
        return db[name]
    except (KeyError, TypeError, AttributeError):
        return None


def _normalize_descriptive_list(value):
    if isinstance(value, list):
        return value
    text = str(value or "").strip()
    if not text:
        return []
    return [{"description": text}]


def _normalize_opening_rows(value):
    if isinstance(value, list):
        return value
    text = str(value or "").strip()
    if not text or text.upper() == "NIL" or text in {"[]", "{}"}:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _normalize_total_service(value):
    if isinstance(value, dict):
        return value
    text = str(value or "").strip()
    if not text or text.upper() == "NIL" or text in {"[]", "{}"}:
        return {"years": 0, "months": 0, "days": 0}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"years": 0, "months": 0, "days": 0}
    return parsed if isinstance(parsed, dict) else {"years": 0, "months": 0, "days": 0}


def _supporting_documents(opening: dict, *, part_id: str) -> list[dict]:
    documents = opening.get("documents") or []
    return [dict(document) for document in documents if (document or {}).get("part_id") == part_id]


async def _upsert_projection_entry(
    *,
    db,
    employee_id: str,
    schema_key: str,
    part_key: str,
    entry_kind: str,
    payload: dict,
    opening: dict,
    opening_id: str,
    current_actor_id: str,
    current_timestamp: str,
    source_index: int | None = None,
) -> None:
    collection = _collection(db, "service_book_entries")
    if collection is None:
        raise RuntimeError("Database handle is missing service_book_entries")

    query = {
        "employee_id": employee_id,
        "schema_key": schema_key,
        "source_opening_id": opening_id,
    }
    identifier_suffix = schema_key
    if source_index is not None:
        query["source_opening_index"] = source_index
        identifier_suffix = f"{schema_key}:{source_index}"

    document = {
        "id": f"{opening_id}:{identifier_suffix}",
        "employee_id": employee_id,
        "part_key": part_key,
        "schema_key": schema_key,
        "schema_version": 1,
        "entry_kind": entry_kind,
        "payload": payload,
        "status": "LOCKED",
        "workflow_state": "LOCKED",
        "is_active": True,
        "source_opening_id": opening_id,
        "supersedes_entry_id": None,
        "created_at": opening.get("submitted_at") or opening.get("created_at") or current_timestamp,
        "created_by": opening.get("submitted_by") or opening.get("updated_by") or current_actor_id,
        "submitted_at": opening.get("submitted_at") or current_timestamp,
        "submitted_by": opening.get("submitted_by") or current_actor_id,
        "verified_at": opening.get("verified_at"),
        "verified_by": opening.get("verified_by"),
        "approved_at": current_timestamp,
        "approved_by": current_actor_id,
        "locked_at": current_timestamp,
        "locked_by": current_actor_id,
        "updated_at": current_timestamp,
        "updated_by": current_actor_id,
    }
    if source_index is not None:
        document["source_opening_index"] = source_index

    await collection.update_one(query, {"$set": document}, upsert=True)


async def _project_locked_opening(*, db, employee_id: str, identity: dict, opening: dict, current_user: dict) -> None:
    parts = normalize_parts(opening.get("parts"))
    now = opening.get("approved_at") or opening.get("updated_at") or now_iso()
    opening_id = str(opening.get("opening_id") or opening.get("id") or f"SBO-{employee_id}")
    current_actor_id = actor_id(current_user)

    summary_repository = EmployeeServiceSummaryRepository(db=db)
    employment_type_code = str(
        identity.get("current_employment_type_code")
        or identity.get("employment_type_code")
        or identity.get("employment_type")
        or "REGULAR"
    ).strip().upper() or "REGULAR"
    await summary_repository.upsert_summary(
        employee_id=employee_id,
        summary={
            "employee_code": identity.get("employee_code") or opening.get("employee_code"),
            "current_employment_type_code": employment_type_code,
            "current_employment_class": "REGULAR",
            "current_service_status": "IN_SERVICE",
            "eligible_for_service_book": True,
            "source_record_id": opening_id,
            "last_projected_at": now,
            "projection_warnings": [],
        },
    )

    part_i = dict(parts.get("part_i") or {})
    if part_i:
        if part_i.get("father_name") and not part_i.get("parent_name"):
            part_i["parent_name"] = part_i.get("father_name")
        if any(part_i.get(key) for key in ("permanent_address_line1", "permanent_address_line2", "permanent_city", "permanent_state_code", "permanent_pincode", "permanent_country")):
            part_i.setdefault(
                "permanent_address",
                {
                    "line1": part_i.get("permanent_address_line1"),
                    "line2": part_i.get("permanent_address_line2"),
                    "city": part_i.get("permanent_city"),
                    "state": part_i.get("permanent_state_code"),
                    "pin": part_i.get("permanent_pincode"),
                    "country": part_i.get("permanent_country"),
                },
            )
        part_i["educational_qualifications_initial"] = _normalize_descriptive_list(part_i.get("educational_qualifications_initial"))
        part_i["educational_qualifications_acquired"] = _normalize_descriptive_list(part_i.get("educational_qualifications_acquired"))
        part_i["professional_qualifications"] = _normalize_descriptive_list(part_i.get("professional_qualifications"))
        await _upsert_projection_entry(
            db=db,
            employee_id=employee_id,
            schema_key="SB_I_BIODATA",
            part_key="SB_PART_I",
            entry_kind="SNAPSHOT",
            payload=part_i,
            opening=opening,
            opening_id=opening_id,
            current_actor_id=current_actor_id,
            current_timestamp=now,
        )

    part_iia = dict(parts.get("part_iia") or {})
    if part_iia:
        if part_iia.get("police_verification_date") and "police_verification_done" not in part_iia:
            part_iia["police_verification_done"] = True
        if part_iia.get("oath_of_allegiance_date") and "oath_of_allegiance_taken" not in part_iia:
            part_iia["oath_of_allegiance_taken"] = True
        if part_iia.get("oath_of_secrecy_date") and "oath_of_secrecy_taken" not in part_iia:
            part_iia["oath_of_secrecy_taken"] = True
        supporting_documents = _supporting_documents(opening, part_id="part_iia")
        if supporting_documents:
            part_iia["supporting_documents"] = supporting_documents
        await _upsert_projection_entry(
            db=db,
            employee_id=employee_id,
            schema_key="SB_IIA_IMMUTABLE_CERTS",
            part_key="SB_PART_II_A",
            entry_kind="SNAPSHOT",
            payload=part_iia,
            opening=opening,
            opening_id=opening_id,
            current_actor_id=current_actor_id,
            current_timestamp=now,
        )

    part_iib = dict(parts.get("part_iib") or {})
    if part_iib:
        await _upsert_projection_entry(
            db=db,
            employee_id=employee_id,
            schema_key="SB_IIB_FAMILY_SHEET",
            part_key="SB_PART_II_B",
            entry_kind="SHEET",
            payload=part_iib,
            opening=opening,
            opening_id=opening_id,
            current_actor_id=current_actor_id,
            current_timestamp=now,
        )

    part_iii = dict(parts.get("part_iii") or {})
    previous_services = _normalize_opening_rows(part_iii.get("previous_services"))
    foreign_services = _normalize_opening_rows(part_iii.get("foreign_services"))
    for index, row in enumerate(previous_services):
        await _upsert_projection_entry(
            db=db,
            employee_id=employee_id,
            schema_key="SB_III_PREVIOUS_SERVICE_ROW",
            part_key="SB_PART_III",
            entry_kind="ROW",
            payload=dict(row),
            opening=opening,
            opening_id=opening_id,
            current_actor_id=current_actor_id,
            current_timestamp=now,
            source_index=index,
        )
    for index, row in enumerate(foreign_services):
        await _upsert_projection_entry(
            db=db,
            employee_id=employee_id,
            schema_key="SB_III_FOREIGN_SERVICE_ROW",
            part_key="SB_PART_III",
            entry_kind="ROW",
            payload=dict(row),
            opening=opening,
            opening_id=opening_id,
            current_actor_id=current_actor_id,
            current_timestamp=now,
            source_index=index,
        )

    if part_iii or previous_services or foreign_services:
        summary_payload = {
            "total_previous_qualifying_service": _normalize_total_service(part_iii.get("total_previous_qualifying_service")),
            "verified": True,
            "verified_by": opening.get("verified_by") or current_actor_id,
            "verification_date": opening.get("verified_at") or now,
        }
        await _upsert_projection_entry(
            db=db,
            employee_id=employee_id,
            schema_key="SB_III_TOTAL_QS_SUMMARY",
            part_key="SB_PART_III",
            entry_kind="SNAPSHOT",
            payload=summary_payload,
            opening=opening,
            opening_id=opening_id,
            current_actor_id=current_actor_id,
            current_timestamp=now,
        )


async def transition(
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
    identity = await resolve_identity_or_404(db, employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_permissions(current_user, permission)
    require_regular_opening(identity)
    opening = await find_opening(db, resolved_id)
    if not opening:
        raise HTTPException(status_code=404, detail="Service Book Opening draft not found")
    status = normalize_status(opening.get("status"))
    if status != from_status:
        raise HTTPException(status_code=409, detail=f"Service Book Opening must be {from_status} before this action")
    parts = normalize_parts(opening.get("parts"))
    if to_status == "SUBMITTED":
        missing = missing_required_parts(parts)
        if missing:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "SERVICE_BOOK_OPENING_INCOMPLETE", "missing": missing},
            )
    now = now_iso()
    opening.update(
        {
            "status": to_status,
            "workflow_status": to_status,
            "remarks": remarks.remarks or "",
            timestamp_field: now,
            actor_field: actor_id(current_user),
            "updated_at": now,
        }
    )
    saved = await save_opening(db, opening)
    if to_status == "LOCKED":
        await _project_locked_opening(
            db=db,
            employee_id=resolved_id,
            identity=identity,
            opening=saved,
            current_user=current_user,
        )
    return opening_response(saved, employee_id=resolved_id, identity=identity)
