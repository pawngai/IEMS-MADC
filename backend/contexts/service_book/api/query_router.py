from __future__ import annotations

from typing import Any

from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.employee_identity.contracts.identity_directory import find_identities_by_ids, resolve_identity_ref
from contexts.rbac.application.access_control import require_owner_or_permissions, require_permissions
from contexts.rbac.domain.models import Permission
from contexts.service_book.application.dto.filters import (
    ServiceBookFilter,
    parse_status_filters,
)
from contexts.service_book.application.errors import ServiceBookApplicationError
from contexts.service_book.application.queries.service_book_queries import (
    ServiceBookQueryUseCases,
)
from contexts.service_book.application.service import validateServiceBookEligibility
from contexts.service_book.read_side.application.factory import (
    build_service_book_service,
)
from contexts.service_book.repository.mongo_entry_repository import MongoServiceBookEntryRepository
from contexts.service_book.records.contracts.service_summary_directory import (
    get_employee_service_summary,
)
from fastapi import APIRouter, Depends, HTTPException


service_book_query_router = APIRouter()


def get_service_book_service(db=Depends(get_db)):
    return build_service_book_service(db=db)


def get_service_book_query_use_cases(
    db=Depends(get_db),
    service=Depends(get_service_book_service),
) -> ServiceBookQueryUseCases:
    return ServiceBookQueryUseCases(
        db=db,
        read_service=service,
        entry_repo=MongoServiceBookEntryRepository(db=db),
    )


def _raise_http(exc: ServiceBookApplicationError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def _require_service_book_read_access(current_user: dict, employee_id: str) -> None:
    require_owner_or_permissions(
        current_user,
        employee_id,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.SERVICE_BOOK_READ_ALL,
    )


async def _resolve_employee(db, employee_ref: str) -> tuple[str, dict[str, Any]]:
    identity = await resolve_identity_ref(db, ref=employee_ref)
    if not identity:
        raise HTTPException(status_code=404, detail="Employee not found")
    return identity["employee_id"], identity


async def _service_book_eligibility_subject(db, *, employee_id: str, identity: dict[str, Any]) -> dict[str, Any]:
    summary = await get_employee_service_summary(db, employee_id=employee_id)
    if summary is not None:
        return summary
    return identity


def _resolve_part_code(service, part_value: str | None) -> str | None:
    return service.normalize_part_code(part_value) if part_value else None


def _parse_workflow_states(value: str | None) -> list[str] | None:
    states = [
        state.strip().upper()
        for state in str(value or "").split(",")
        if state.strip()
    ]
    return states or None


@service_book_query_router.get("/employees/{employee_id}")
async def get_service_book(
    employee_id: str,
    query_use_cases: ServiceBookQueryUseCases = Depends(get_service_book_query_use_cases),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await query_use_cases.get_service_book(
            employee_ref=employee_id,
            current_user=current_user,
        )
    except ServiceBookApplicationError as exc:
        _raise_http(exc)


@service_book_query_router.get("/employees/{employee_id}/parts/{part_code}")
async def get_service_book_part(
    employee_id: str,
    part_code: str,
    query_use_cases: ServiceBookQueryUseCases = Depends(get_service_book_query_use_cases),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await query_use_cases.get_part(
            employee_ref=employee_id,
            part_code=part_code,
            current_user=current_user,
        )
    except ServiceBookApplicationError as exc:
        _raise_http(exc)


@service_book_query_router.get("/employees/{employee_id}/entries")
async def list_service_book_entries(
    employee_id: str,
    part_code: str | None = None,
    status: str | None = None,
    statuses: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    db=Depends(get_db),
    service=Depends(get_service_book_service),
    query_use_cases: ServiceBookQueryUseCases | None = Depends(get_service_book_query_use_cases),
    current_user: dict = Depends(get_current_user),
):
    parsed_status, parsed_statuses = parse_status_filters(status, statuses)
    filters = ServiceBookFilter(
        part_code=_resolve_part_code(service, part_code),
        status=parsed_status,
        statuses=parsed_statuses,
        from_date=from_date,
        to_date=to_date,
    )
    if query_use_cases is not None and not hasattr(query_use_cases, "dependency"):
        try:
            return await query_use_cases.list_entries(
                employee_ref=employee_id,
                filters=filters,
                current_user=current_user,
            )
        except ServiceBookApplicationError as exc:
            _raise_http(exc)

    resolved_id, identity = await _resolve_employee(db, employee_id)
    _require_service_book_read_access(current_user, resolved_id)
    validateServiceBookEligibility(
        await _service_book_eligibility_subject(db, employee_id=resolved_id, identity=identity)
    )
    return await service.list_service_book_entries(
        employee_id=resolved_id,
        filters=filters.model_dump(exclude_none=True),
    )


@service_book_query_router.get("/queue")
async def list_service_book_queue(
    workflow_state: str | None = None,
    workflow_states: str | None = None,
    page_size: int = 200,
    db=Depends(get_db),
    query_use_cases: ServiceBookQueryUseCases | None = Depends(get_service_book_query_use_cases),
    current_user: dict = Depends(get_current_user),
):
    parsed_workflow_states = _parse_workflow_states(workflow_states)
    if query_use_cases is not None and not hasattr(query_use_cases, "dependency"):
        try:
            return await query_use_cases.list_queue(
                workflow_state=workflow_state,
                workflow_states=parsed_workflow_states,
                page_size=page_size,
                current_user=current_user,
            )
        except ServiceBookApplicationError as exc:
            _raise_http(exc)

    require_permissions(current_user, Permission.SERVICE_BOOK_READ_ALL)
    entries = await MongoServiceBookEntryRepository(db=db).list_queue_entries(
        workflow_state=workflow_state,
        workflow_states=parsed_workflow_states,
        page_size=page_size,
    )
    if not entries:
        return {"entries": []}
    employee_ids = list({entry["employee_id"] for entry in entries})
    identities = await find_identities_by_ids(
        db,
        employee_ids=employee_ids,
        projection={"_id": 0, "employee_id": 1, "full_name": 1, "employee_code": 1},
    )
    id_map = {identity["employee_id"]: identity for identity in identities}
    enriched_entries = []
    for entry in entries:
        ident = id_map.get(entry["employee_id"])
        if not ident:
            continue
        enriched = dict(entry)
        enriched["full_name"] = ident.get("full_name", "")
        enriched["employee_code"] = ident.get("employee_code", "")
        enriched_entries.append(enriched)
    return {"entries": enriched_entries}


@service_book_query_router.get("/parts/{part_key}/schema")
async def get_service_book_part_schema(
    part_key: str,
    query_use_cases: ServiceBookQueryUseCases = Depends(get_service_book_query_use_cases),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await query_use_cases.get_schema(
            part_key=part_key,
            current_user=current_user,
        )
    except ServiceBookApplicationError as exc:
        _raise_http(exc)


@service_book_query_router.get("/employees/{employee_id}/part-i/defaults")
async def get_part_i_defaults(
    employee_id: str,
    query_use_cases: ServiceBookQueryUseCases = Depends(get_service_book_query_use_cases),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await query_use_cases.get_part_i_defaults(
            employee_ref=employee_id,
            current_user=current_user,
        )
    except ServiceBookApplicationError as exc:
        _raise_http(exc)
