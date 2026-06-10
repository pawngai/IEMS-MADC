"""Document attachment locking bridge for approved change requests."""

from __future__ import annotations

async def lock_documents_for_approved_request(
    attachments: list[dict], *, request_id: str, status: str, db=None
) -> None:
    from contexts.documents.contracts.document_lock import (
        lock_documents_for_approved_request as lock_documents,
    )

    await lock_documents(
        attachments,
        request_id=request_id,
        status=status,
        db=db,
    )
