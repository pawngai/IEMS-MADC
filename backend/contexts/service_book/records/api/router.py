from __future__ import annotations

from contexts.service_book.records.api.dependencies import (
    actor_id_from_user,
    event_id_command,
    get_service_events_service,
)
from contexts.service_book.records.application.service_summary_projection import (
    EmployeeServiceSummaryProjectionService,
    is_service_summary_projectable,
    normalize_record_type,
)
from contexts.service_book.records.application.commands.attach_document import AttachDocumentCommand
from contexts.service_book.records.application.commands.approve_event import (
    ApproveServiceEventCommand,
    LockServiceEventCommand,
)
from contexts.service_book.records.application.commands.record_event import RecordServiceEventCommand
from contexts.service_book.records.application.commands.revise_event import ReviseServiceEventCommand
from contexts.service_book.records.application.commands.submit_event import SubmitServiceEventCommand
from contexts.service_book.records.application.commands.verify_event import VerifyServiceEventCommand
from contexts.service_book.records.application.commands.void_event import VoidServiceEventCommand
from contexts.service_book.records.application.service import ServiceEventApplicationService
from contexts.service_book.records.schemas.service_event_schemas import get_service_event_form_schema
from contexts.employee_identity.contracts.identity_directory import resolve_identity_ref
from fastapi import APIRouter, Depends, HTTPException
from contexts.rbac.domain.models import Permission
from contexts.rbac.application.access_control import require_owner_or_permissions, require_permissions
from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.service_book.records.repository.service_summary_repository import (
    EmployeeServiceSummaryRepository,
)
from shared_kernel.base import DomainError


service_book_records_command_router = APIRouter(prefix="/records", tags=["Service Book Records"])
service_records_router = APIRouter(prefix="/service-records", tags=["Service Records"])
employee_service_summaries_router = APIRouter(
    prefix="/employee-service-summaries",
    tags=["Employee Service Summaries"],
)


def _service_event_http_exception(exc: DomainError | ValueError) -> HTTPException:
    message = str(exc).strip() or "Service event request failed"
    normalized = message.lower()
    if "not found" in normalized:
        return HTTPException(
            status_code=404,
            detail={
                "error_code": "SERVICE_EVENT_NOT_FOUND",
                "message": message,
            },
        )
    return HTTPException(
        status_code=409,
        detail={
            "error_code": "SERVICE_EVENT_CONFLICT",
            "message": message,
        },
    )


async def _call_service(operation):
    try:
        return await operation
    except HTTPException:
        raise
    except (DomainError, ValueError) as exc:
        raise _service_event_http_exception(exc) from exc


async def _resolve_existing_employee_identity(*, db, employee_ref: str) -> dict:
    identity = await resolve_identity_ref(db, ref=employee_ref)
    resolved_id = str((identity or {}).get("employee_id") or "").strip()
    if resolved_id:
        return identity
    raise HTTPException(
        status_code=404,
        detail={
            "error_code": "EMPLOYEE_NOT_FOUND",
            "message": f"Employee '{employee_ref}' not found",
        },
    )


def _require_regular_service_events_employee(identity: dict | None) -> None:
    employment_type = str(
        (identity or {}).get("current_employment_type_code")
        or (identity or {}).get("employment_type")
        or (identity or {}).get("employment_type_code")
        or ""
    ).strip().upper()
    if employment_type in {"REGULAR", "REG"}:
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error": "Service Events not applicable",
            "message": "Service Events are only maintained for REGULAR employees.",
            "required_employment_type": "REGULAR",
        },
    )


def _is_service_record_payload(payload: RecordServiceEventCommand) -> bool:
    return is_service_summary_projectable(
        normalize_record_type(payload.record_type, event_type=payload.event_type.value),
    )


def _require_service_record_payload(payload: RecordServiceEventCommand) -> None:
    if _is_service_record_payload(payload):
        return
    raise HTTPException(
        status_code=422,
        detail="Service records endpoint only accepts engagement, termination, or regularisation records.",
    )


def _validate_service_event_part_code(part_code: str | None) -> None:
    """All service events record to Part IV: History of Service."""
    normalized = str(part_code or "").strip().upper()
    if not normalized or normalized == "IV":
        return
    raise HTTPException(
        status_code=409,
        detail=f"Service events must target Part IV. Got: '{part_code}'",
    )


@service_book_records_command_router.get("/schema")
async def get_service_event_schema(current_user: dict = Depends(get_current_user)):
    require_permissions(current_user, Permission.SERVICE_BOOK_READ_ALL)
    return get_service_event_form_schema()


@service_book_records_command_router.post("")
@service_book_records_command_router.post("/record")
async def record_service_event(
    payload: RecordServiceEventCommand,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    actor_id = actor_id_from_user(current_user)
    _validate_service_event_part_code(payload.part_code)
    identity = await _resolve_existing_employee_identity(db=db, employee_ref=payload.employee_id)
    if not _is_service_record_payload(payload):
        _require_regular_service_events_employee(identity)
    resolved_id = str(identity.get("employee_id") or "").strip()
    payload = payload.model_copy(update={"employee_id": resolved_id})
    require_owner_or_permissions(
        current_user,
        resolved_id,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_READ_ALL,
    )
    return await _call_service(service.record(command=payload, actor_id=actor_id))


async def _record_service_record_common(
    *,
    payload: RecordServiceEventCommand,
    service: ServiceEventApplicationService,
    current_user: dict,
    db,
):
    actor_id = actor_id_from_user(current_user)
    _require_service_record_payload(payload)
    identity = await _resolve_existing_employee_identity(db=db, employee_ref=payload.employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    payload = payload.model_copy(update={"employee_id": resolved_id})
    require_owner_or_permissions(
        current_user,
        resolved_id,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_READ_ALL,
    )
    return await _call_service(service.record(command=payload, actor_id=actor_id))


@service_records_router.post("")
async def record_service_record(
    payload: RecordServiceEventCommand,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _record_service_record_common(
        payload=payload,
        service=service,
        current_user=current_user,
        db=db,
    )


@service_records_router.get("/employees/{employee_id}")
async def get_service_records_for_employee(
    employee_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    identity = await _resolve_existing_employee_identity(db=db, employee_ref=employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(
        current_user,
        resolved_id,
        Permission.SERVICE_BOOK_READ_ALL,
    )
    return await _call_service(service.get_stream(employee_id=resolved_id))


@service_records_router.post("/{record_id}/submit")
async def submit_service_record(
    record_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_SUBMIT)
    return await _call_service(service.submit(
        command=event_id_command(SubmitServiceEventCommand, record_id),
        actor_id=actor_id,
    ))


@service_records_router.post("/{record_id}/verify")
async def verify_service_record(
    record_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_VERIFY)
    return await _call_service(service.verify(
        command=event_id_command(VerifyServiceEventCommand, record_id),
        actor_id=actor_id,
    ))


@service_records_router.post("/{record_id}/approve")
async def approve_service_record(
    record_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_APPROVE)
    return await _call_service(service.approve(
        command=event_id_command(ApproveServiceEventCommand, record_id),
        actor_id=actor_id,
    ))


@service_records_router.post("/{record_id}/post")
async def post_service_record(
    record_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_APPROVE)
    return await _call_service(service.lock(
        command=event_id_command(LockServiceEventCommand, record_id),
        actor_id=actor_id,
    ))


@employee_service_summaries_router.get("/{employee_id}")
async def get_employee_service_summary(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> dict | None:
    identity = await _resolve_existing_employee_identity(db=db, employee_ref=employee_id)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(
        current_user,
        resolved_id,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.SERVICE_BOOK_READ_ALL,
    )
    service = EmployeeServiceSummaryProjectionService(
        repository=EmployeeServiceSummaryRepository(db=db),
    )
    summary = await service.get_summary(employee_id=resolved_id)
    return summary


@service_book_records_command_router.patch("/{service_event_id}/correct")
async def correct_service_event(
    service_event_id: str,
    payload: ReviseServiceEventCommand,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(
        current_user,
        Permission.SERVICE_BOOK_SUPERSEDE,
        Permission.SERVICE_BOOK_ENTRY_APPROVE,
    )
    return await _call_service(service.revise(
        command=ReviseServiceEventCommand(
            service_event_id=service_event_id,
            corrected_payload=payload.corrected_payload,
            reason=payload.reason,
        ),
        actor_id=actor_id,
    ))


@service_book_records_command_router.post("/{service_event_id}/void")
async def void_service_event(
    service_event_id: str,
    payload: VoidServiceEventCommand,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(
        current_user,
        Permission.SERVICE_BOOK_SUPERSEDE,
        Permission.SERVICE_BOOK_ENTRY_APPROVE,
    )
    return await _call_service(service.void(
        command=VoidServiceEventCommand(
            service_event_id=service_event_id,
            reason=payload.reason,
        ),
        actor_id=actor_id,
    ))


@service_book_records_command_router.post("/{service_event_id}/documents")
async def attach_service_event_document(
    service_event_id: str,
    payload: AttachDocumentCommand,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(
        current_user,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_VERIFY,
        Permission.SERVICE_BOOK_ENTRY_APPROVE,
    )
    return await _call_service(service.attach_document(
        command=AttachDocumentCommand(
            service_event_id=service_event_id,
            document_id=payload.document_id,
            document_type=payload.document_type,
        ),
        actor_id=actor_id,
    ))


@service_book_records_command_router.get("/employees/{employee_id}")
async def get_service_event_stream(
    employee_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    identity = await _resolve_existing_employee_identity(db=db, employee_ref=employee_id)
    _require_regular_service_events_employee(identity)
    resolved_id = str(identity.get("employee_id") or "").strip()
    require_owner_or_permissions(
        current_user,
        resolved_id,
        Permission.SERVICE_BOOK_READ_ALL,
    )
    return await _call_service(service.get_stream(employee_id=resolved_id))


@service_book_records_command_router.post("/{service_event_id}/approve", include_in_schema=False)
async def approve_service_event(
    service_event_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_APPROVE)
    return await _call_service(service.approve(
        command=event_id_command(ApproveServiceEventCommand, service_event_id),
        actor_id=actor_id,
    ))


@service_book_records_command_router.post("/{service_event_id}/submit")
async def submit_service_event(
    service_event_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_SUBMIT)
    return await _call_service(service.submit(
        command=event_id_command(SubmitServiceEventCommand, service_event_id),
        actor_id=actor_id,
    ))


@service_book_records_command_router.post("/{service_event_id}/verify")
async def verify_service_event(
    service_event_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_VERIFY)
    return await _call_service(service.verify(
        command=event_id_command(VerifyServiceEventCommand, service_event_id),
        actor_id=actor_id,
    ))


@service_book_records_command_router.post("/{service_event_id}/lock")
async def lock_service_event(
    service_event_id: str,
    service: ServiceEventApplicationService = Depends(get_service_events_service),
    current_user: dict = Depends(get_current_user),
):
    actor_id = actor_id_from_user(current_user)
    require_permissions(current_user, Permission.SERVICE_BOOK_ENTRY_APPROVE)
    return await _call_service(service.lock(
        command=event_id_command(LockServiceEventCommand, service_event_id),
        actor_id=actor_id,
    ))

