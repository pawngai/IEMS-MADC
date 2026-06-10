from __future__ import annotations

import uuid

from fastapi import HTTPException

from contexts.seniority.application.commands import GenerateRequest, PromoteRequest, RankOverrideRequest, WorkflowActionRequest
from contexts.seniority.application.seniority_service import gather_employees
from contexts.seniority.domain.rank_policy import apply_rank_overrides
from contexts.seniority.domain.seniority_list import actor_id, actor_name, now_iso
from contexts.seniority.domain.seniority_policy import (
    PROMOTION_ORDER,
    ROLE_APPROVER,
    ROLE_DATA_ENTRY_SET,
    ROLE_VERIFIER,
    validate_list_type,
    require_role,
)
from contexts.seniority.domain.workflow_policy import require_separation_of_duties, require_status
from contexts.seniority.infrastructure.seniority_repository import get_list, insert_list, update_list


async def generate_seniority_list(*, db, current_user: dict, payload: GenerateRequest) -> dict:
    require_role(current_user, ROLE_DATA_ENTRY_SET, "generate seniority list")
    list_type = validate_list_type(payload.list_type)

    employees = await gather_employees(db, payload.service, payload.designation_code)
    if not employees:
        raise HTTPException(400, "No matching employees found for given service and designation")

    now = now_iso()
    actor = actor_id(current_user)
    list_id = str(uuid.uuid4())
    type_label = list_type.capitalize()
    desg_part = f" / {payload.designation_code}" if payload.designation_code else ""
    title = payload.title or f"{type_label} Seniority - {payload.service}{desg_part}"

    doc = {
        "list_id": list_id,
        "title": title,
        "list_type": list_type,
        "service": payload.service,
        "designation_code": payload.designation_code or "",
        "status": "DRAFT",
        "employees": employees,
        "total": len(employees),
        "created_at": now,
        "created_by": actor,
        "created_by_name": actor_name(current_user),
        "updated_at": now,
        "updated_by": actor,
        "submitted_at": None,
        "submitted_by": None,
        "submitted_by_name": None,
        "verified_at": None,
        "verified_by": None,
        "verified_by_name": None,
        "approved_at": None,
        "approved_by": None,
        "approved_by_name": None,
        "remarks": None,
        "version": 1,
        "promoted_from": None,
    }
    return await insert_list(db, doc)


async def override_ranks(*, db, current_user: dict, list_id: str, payload: RankOverrideRequest) -> dict:
    require_role(current_user, ROLE_DATA_ENTRY_SET, "override seniority ranks")
    doc = await get_list(db, list_id)
    if doc.get("list_type", "DRAFT") == "FINAL":
        raise HTTPException(400, "Cannot edit ranks on a FINAL seniority list")
    if doc["status"] not in ("DRAFT", "REJECTED"):
        raise HTTPException(400, f"Cannot edit ranks in {doc['status']} status")

    employees = apply_rank_overrides(employees=doc["employees"], overrides=payload.overrides)
    await update_list(
        db,
        list_id,
        {
            "employees": employees,
            "updated_at": now_iso(),
            "updated_by": actor_id(current_user),
        },
    )
    return {"status": "ok", "message": f"{len(payload.overrides)} rank(s) updated"}


async def submit_seniority_list(*, db, current_user: dict, list_id: str, payload: WorkflowActionRequest) -> dict:
    require_role(current_user, ROLE_DATA_ENTRY_SET, "submit seniority list")
    doc = await get_list(db, list_id)
    require_status(doc, ("DRAFT", "REJECTED"), "submit")
    now = now_iso()
    actor = actor_id(current_user)
    await update_list(
        db,
        list_id,
        {
            "status": "SUBMITTED",
            "submitted_at": now,
            "submitted_by": actor,
            "submitted_by_name": actor_name(current_user),
            "updated_at": now,
            "updated_by": actor,
            "remarks": payload.remarks,
        },
    )
    return {"status": "SUBMITTED", "list_id": list_id}


async def verify_seniority_list(*, db, current_user: dict, list_id: str, payload: WorkflowActionRequest) -> dict:
    require_role(current_user, {ROLE_VERIFIER}, "verify seniority list")
    doc = await get_list(db, list_id)
    require_status(doc, ("SUBMITTED",), "verify")
    actor = actor_id(current_user)
    require_separation_of_duties(doc, actor, action="verify")
    now = now_iso()
    await update_list(
        db,
        list_id,
        {
            "status": "VERIFIED",
            "verified_at": now,
            "verified_by": actor,
            "verified_by_name": actor_name(current_user),
            "updated_at": now,
            "updated_by": actor,
            "remarks": payload.remarks,
        },
    )
    return {"status": "VERIFIED", "list_id": list_id}


async def approve_seniority_list(*, db, current_user: dict, list_id: str, payload: WorkflowActionRequest) -> dict:
    require_role(current_user, {ROLE_APPROVER}, "approve seniority list")
    doc = await get_list(db, list_id)
    require_status(doc, ("VERIFIED",), "approve")
    actor = actor_id(current_user)
    require_separation_of_duties(doc, actor, action="approve")
    now = now_iso()
    await update_list(
        db,
        list_id,
        {
            "status": "APPROVED",
            "approved_at": now,
            "approved_by": actor,
            "approved_by_name": actor_name(current_user),
            "updated_at": now,
            "updated_by": actor,
            "remarks": payload.remarks,
        },
    )
    return {"status": "APPROVED", "list_id": list_id}


async def reject_seniority_list(*, db, current_user: dict, list_id: str, payload: WorkflowActionRequest) -> dict:
    require_role(current_user, {ROLE_VERIFIER, ROLE_APPROVER}, "reject seniority list")
    doc = await get_list(db, list_id)
    require_status(doc, ("SUBMITTED", "VERIFIED"), "reject")
    now = now_iso()
    actor = actor_id(current_user)
    await update_list(
        db,
        list_id,
        {
            "status": "REJECTED",
            "updated_at": now,
            "updated_by": actor,
            "remarks": payload.remarks,
        },
    )
    return {"status": "REJECTED", "list_id": list_id}


async def promote_seniority_list(*, db, current_user: dict, list_id: str, payload: PromoteRequest) -> dict:
    require_role(current_user, ROLE_DATA_ENTRY_SET, "promote seniority list")
    doc = await get_list(db, list_id)

    if doc["status"] != "APPROVED":
        raise HTTPException(400, "Only APPROVED lists can be promoted")

    current_type = doc.get("list_type", "DRAFT")
    next_type = PROMOTION_ORDER.get(current_type)
    if not next_type:
        raise HTTPException(400, f"Cannot promote from {current_type} - already at FINAL")

    now = now_iso()
    actor = actor_id(current_user)
    new_list_id = str(uuid.uuid4())
    type_label = next_type.capitalize()
    new_title = f"{type_label} Seniority - {doc['service']} / {doc['designation_code']}"

    new_doc = {
        "list_id": new_list_id,
        "title": new_title,
        "list_type": next_type,
        "service": doc["service"],
        "designation_code": doc["designation_code"],
        "status": "DRAFT",
        "employees": doc["employees"],
        "total": doc["total"],
        "created_at": now,
        "created_by": actor,
        "created_by_name": actor_name(current_user),
        "updated_at": now,
        "updated_by": actor,
        "submitted_at": None,
        "submitted_by": None,
        "submitted_by_name": None,
        "verified_at": None,
        "verified_by": None,
        "verified_by_name": None,
        "approved_at": None,
        "approved_by": None,
        "approved_by_name": None,
        "remarks": payload.remarks,
        "version": doc.get("version", 1) + 1,
        "promoted_from": list_id,
    }
    return await insert_list(db, new_doc)
