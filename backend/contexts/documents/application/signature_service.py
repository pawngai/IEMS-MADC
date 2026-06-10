"""Documents application — signature request orchestration."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from contexts.documents.domain.signature_request import (
    SIGNATURE_STATUS_CANCELLED,
    SIGNATURE_STATUS_COMPLETED,
    SIGNATURE_STATUS_DECLINED,
    SIGNATURE_STATUS_PENDING,
    SignatureRequest,
    assert_can_sign,
    validate_signers,
)
from contexts.documents.infrastructure.access_control import (
    can_manage_all_documents,
    get_employee_id,
    get_user_id,
)
from contexts.documents.infrastructure.lock_ops import lock_documents_for_approved_request
from contexts.documents.infrastructure.metadata_ops import read_document_metadata
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.documents.infrastructure.storage_ops import storage
from contexts.documents.repository.signature_request_repository import SignatureRequestRepository
from fastapi import HTTPException


def _require_issuer_permission(current_user: dict, *, metadata: dict) -> None:
    if can_manage_all_documents(current_user):
        return
    # Owners may request signatures on their own documents.
    if str(metadata.get("uploaded_employee_id") or "") == get_employee_id(current_user):
        return
    raise HTTPException(
        status_code=403,
        detail="Only managers or the document owner may request signatures",
    )


async def create_signature_request(
    *,
    filename: str,
    signers_input: list[dict[str, Any]],
    deadline_at: str | None,
    current_user: dict,
    db,
) -> dict[str, Any]:
    if not storage().exists(StorageBucket.DOCUMENT, filename):
        raise HTTPException(status_code=404, detail="Document not found")
    metadata = await read_document_metadata(filename, db=db) or {}
    _require_issuer_permission(current_user, metadata=metadata)

    try:
        signers = validate_signers(signers_input)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    request = SignatureRequest(
        request_id=uuid.uuid4().hex,
        document_id=str(metadata.get("document_id") or filename),
        filename=filename,
        status=SIGNATURE_STATUS_PENDING,
        issuer_user_id=get_user_id(current_user) or None,
        issuer_employee_id=get_employee_id(current_user) or None,
        created_at=datetime.now(timezone.utc).isoformat(),
        deadline_at=deadline_at,
        signers=signers,
    )
    await SignatureRequestRepository(db=db).upsert(request)
    return _to_response(request)


async def sign_signature_request(
    *,
    request_id: str,
    signature_filename: str | None,
    current_user: dict,
    db,
) -> dict[str, Any]:
    repo = SignatureRequestRepository(db=db)
    request = await repo.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Signature request not found")

    signer_employee_id = get_employee_id(current_user)
    try:
        idx = assert_can_sign(request, signer_employee_id=signer_employee_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    now = datetime.now(timezone.utc).isoformat()
    signer = request.signers[idx]
    signer.signed_at = now
    signer.signature_filename = signature_filename

    if request.current_signer_index() is None:
        request.status = SIGNATURE_STATUS_COMPLETED
        request.completed_at = now
        # Final signing locks the document so further mutation is blocked.
        await lock_documents_for_approved_request(
            [{"filename": request.filename}],
            request_id=request.request_id,
            status="APPROVED",
            db=db,
            lock_reason="SIGNATURE_REQUEST_COMPLETED",
        )

    await repo.upsert(request)
    return _to_response(request)


async def decline_signature_request(
    *,
    request_id: str,
    reason: str,
    current_user: dict,
    db,
) -> dict[str, Any]:
    repo = SignatureRequestRepository(db=db)
    request = await repo.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Signature request not found")

    signer_employee_id = get_employee_id(current_user)
    try:
        idx = assert_can_sign(request, signer_employee_id=signer_employee_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    now = datetime.now(timezone.utc).isoformat()
    request.signers[idx].declined_at = now
    request.signers[idx].decline_reason = reason.strip() or None
    request.status = SIGNATURE_STATUS_DECLINED
    request.completed_at = now
    await repo.upsert(request)
    return _to_response(request)


async def cancel_signature_request(
    *,
    request_id: str,
    current_user: dict,
    db,
) -> dict[str, Any]:
    repo = SignatureRequestRepository(db=db)
    request = await repo.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Signature request not found")
    if not request.is_pending():
        raise HTTPException(status_code=409, detail=f"Request is already {request.status}")

    is_issuer = request.issuer_user_id == get_user_id(current_user)
    if not (is_issuer or can_manage_all_documents(current_user)):
        raise HTTPException(status_code=403, detail="Only the issuer or a document manager may cancel")

    request.status = SIGNATURE_STATUS_CANCELLED
    request.completed_at = datetime.now(timezone.utc).isoformat()
    await repo.upsert(request)
    return _to_response(request)


async def list_pending_for_current_user(*, current_user: dict, db) -> list[dict[str, Any]]:
    employee_id = get_employee_id(current_user)
    if not employee_id:
        return []
    pending = await SignatureRequestRepository(db=db).list_pending_for_signer(employee_id)
    return [_to_response(req) for req in pending]


def _to_response(request: SignatureRequest) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "document_id": request.document_id,
        "filename": request.filename,
        "status": request.status,
        "issuer_user_id": request.issuer_user_id,
        "issuer_employee_id": request.issuer_employee_id,
        "created_at": request.created_at,
        "deadline_at": request.deadline_at,
        "completed_at": request.completed_at,
        "current_signer_index": request.current_signer_index(),
        "signers": [
            {
                "employee_id": s.employee_id,
                "role": s.role,
                "signed_at": s.signed_at,
                "signature_filename": s.signature_filename,
                "declined_at": s.declined_at,
                "decline_reason": s.decline_reason,
            }
            for s in request.signers
        ],
    }
