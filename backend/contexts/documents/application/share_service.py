"""Documents application — share-link orchestration."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app_platform.config.settings import settings
from contexts.documents.domain.share_token import (
    SHARE_SCOPE_INLINE,
    clamp_ttl_seconds,
    is_expired,
    issue_token,
    parse_token,
)
from contexts.documents.domain.validation import (
    is_document_owner,
    is_legal_hold_active,
)
from contexts.documents.infrastructure.access_control import can_manage_all_documents
from contexts.documents.infrastructure.metadata_ops import (
    read_document_metadata,
    write_document_metadata,
)
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.documents.infrastructure.storage_ops import content_type_for_doc, storage
from fastapi import HTTPException

_NONCE_FIELD = "share_token_nonces"
_REVOKED_FIELD = "share_token_revoked_nonces"


def _require_issuance_permission(current_user: dict, metadata: dict) -> None:
    if can_manage_all_documents(current_user):
        return
    if is_document_owner(metadata, current_user):
        return
    raise HTTPException(
        status_code=403,
        detail="Only document managers or the document owner may issue a share link",
    )


async def create_document_share_link(
    *,
    filename: str,
    ttl_seconds: int,
    current_user: dict,
    db,
) -> dict:
    if not storage().exists(StorageBucket.DOCUMENT, filename):
        raise HTTPException(status_code=404, detail="Document not found")

    metadata = await read_document_metadata(filename, db=db) or {}
    _require_issuance_permission(current_user, metadata)

    if is_legal_hold_active(metadata):
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "DOCUMENT_LEGAL_HOLD",
                "message": "Cannot issue share links for documents under legal hold",
            },
        )

    ttl = clamp_ttl_seconds(ttl_seconds)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
    document_id = str(metadata.get("document_id") or filename)
    token, nonce = issue_token(
        secret=settings.jwt_secret,
        document_id=document_id,
        filename=filename,
        expires_at=expires_at,
        scope=SHARE_SCOPE_INLINE,
    )

    existing = list(metadata.get(_NONCE_FIELD) or [])
    existing.append(nonce)
    metadata[_NONCE_FIELD] = existing
    await write_document_metadata(filename, metadata, db=db)

    return {
        "success": True,
        "token": token,
        "nonce": nonce,
        "expires_at": expires_at.isoformat(),
        "share_url": f"/api/documents/shares/{token}",
    }


async def revoke_document_share_link(
    *,
    filename: str,
    nonce: str,
    current_user: dict,
    db,
) -> dict:
    metadata = await read_document_metadata(filename, db=db) or {}
    _require_issuance_permission(current_user, metadata)

    revoked = list(metadata.get(_REVOKED_FIELD) or [])
    if nonce not in revoked:
        revoked.append(nonce)
        metadata[_REVOKED_FIELD] = revoked
        await write_document_metadata(filename, metadata, db=db)
    return {"success": True, "nonce": nonce, "revoked": True}


async def resolve_share_token(*, token: str, db):
    try:
        payload = parse_token(secret=settings.jwt_secret, token=token)
    except ValueError:
        raise HTTPException(status_code=404, detail="Share link is invalid")

    if is_expired(payload):
        raise HTTPException(status_code=410, detail="Share link has expired")

    filename = str(payload.get("f") or "").strip()
    nonce = str(payload.get("n") or "").strip()
    if not filename or not nonce:
        raise HTTPException(status_code=404, detail="Share link is invalid")

    if not storage().exists(StorageBucket.DOCUMENT, filename):
        raise HTTPException(status_code=404, detail="Document not found")

    metadata = await read_document_metadata(filename, db=db) or {}
    if is_legal_hold_active(metadata):
        # Treat as 410 — the link existed and was valid once, but the
        # document is now legally held.
        raise HTTPException(status_code=410, detail="Document is no longer accessible")

    revoked = set(metadata.get(_REVOKED_FIELD) or [])
    if nonce in revoked:
        raise HTTPException(status_code=410, detail="Share link has been revoked")

    # Scan-status gate: never serve INFECTED via public share.
    if str(metadata.get("scan_status") or "").upper() == "INFECTED":
        raise HTTPException(status_code=403, detail="Document is quarantined")

    return storage().inline_response(
        StorageBucket.DOCUMENT,
        filename,
        media_type=content_type_for_doc(filename),
    )
