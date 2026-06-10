"""Seniority Management API router.

The router keeps HTTP concerns only. Generation, rank changes, workflow
transitions, promotion, and persistence live in seniority application/domain
layers.
"""

from __future__ import annotations

import csv
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app_platform.auth.current_user import get_current_user
from contexts.seniority.application import seniority_command_service
from contexts.seniority.application import seniority_query_service
from contexts.seniority.application.commands import (
    GenerateRequest,
    PromoteRequest,
    RankOverrideRequest,
    WorkflowActionRequest,
)
from contexts.seniority.domain.rank_policy import apply_rank_overrides as _apply_rank_overrides


def _get_db():
    from app_platform.db.runtime import mongo_state

    if mongo_state.db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    return mongo_state.db


seniority_router = APIRouter(prefix="/seniority", tags=["seniority"])


@seniority_router.post("/generate")
async def generate_seniority_list(
    payload: GenerateRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.generate_seniority_list(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@seniority_router.get("/services")
async def list_available_services(
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_query_service.list_available_services(db=db, current_user=current_user)


@seniority_router.get("/designations")
async def list_available_designations(
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_query_service.list_available_designations(db=db, current_user=current_user)


@seniority_router.get("/lists")
async def list_seniority_lists(
    status: Optional[str] = None,
    service: Optional[str] = None,
    list_type: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_query_service.list_seniority_lists(
        db=db,
        current_user=current_user,
        status=status,
        service=service,
        list_type=list_type,
        year=year,
        limit=limit,
        offset=offset,
    )


@seniority_router.get("/lists/{list_id}")
async def get_seniority_list(
    list_id: str,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_query_service.get_seniority_list(
        db=db,
        current_user=current_user,
        list_id=list_id,
    )


@seniority_router.put("/lists/{list_id}/ranks")
async def override_ranks(
    list_id: str,
    payload: RankOverrideRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.override_ranks(
        db=db,
        current_user=current_user,
        list_id=list_id,
        payload=payload,
    )


@seniority_router.post("/lists/{list_id}/submit")
async def submit_seniority_list(
    list_id: str,
    payload: WorkflowActionRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.submit_seniority_list(
        db=db,
        current_user=current_user,
        list_id=list_id,
        payload=payload,
    )


@seniority_router.post("/lists/{list_id}/verify")
async def verify_seniority_list(
    list_id: str,
    payload: WorkflowActionRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.verify_seniority_list(
        db=db,
        current_user=current_user,
        list_id=list_id,
        payload=payload,
    )


@seniority_router.post("/lists/{list_id}/approve")
async def approve_seniority_list(
    list_id: str,
    payload: WorkflowActionRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.approve_seniority_list(
        db=db,
        current_user=current_user,
        list_id=list_id,
        payload=payload,
    )


@seniority_router.post("/lists/{list_id}/reject")
async def reject_seniority_list(
    list_id: str,
    payload: WorkflowActionRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.reject_seniority_list(
        db=db,
        current_user=current_user,
        list_id=list_id,
        payload=payload,
    )


@seniority_router.post("/lists/{list_id}/promote")
async def promote_seniority_list(
    list_id: str,
    payload: PromoteRequest,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    return await seniority_command_service.promote_seniority_list(
        db=db,
        current_user=current_user,
        list_id=list_id,
        payload=payload,
    )


@seniority_router.get("/lists/{list_id}/export")
async def export_seniority_csv(
    list_id: str,
    db=Depends(_get_db),
    current_user: dict = Depends(get_current_user),
):
    doc = await seniority_query_service.get_seniority_list_for_export(
        db=db,
        current_user=current_user,
        list_id=list_id,
    )

    headers = [
        "rank", "employee_code", "full_name", "gender",
        "employment_type", "department_code", "designation_code",
        "date_of_initial_engagement", "service", "group",
        "mode_of_recruitment", "appointment_date",
        "confirmation_date", "last_promotion_date",
    ]
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for employee in doc.get("employees", []):
        writer.writerow({header: employee.get(header, "") for header in headers})

    buf.seek(0)
    list_type = doc.get("list_type", "DRAFT").lower()
    filename = f"seniority_{list_type}_{doc['service']}_{doc['designation_code']}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
