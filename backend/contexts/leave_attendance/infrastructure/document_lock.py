from __future__ import annotations


async def lock_documents_for_finalized_leave(
    attachments: list[dict], *, leave_id: str, status: str, db=None
) -> None:
    from contexts.documents.contracts.document_lock import (
        lock_documents_for_approved_request as lock_documents,
    )

    await lock_documents(
        attachments,
        request_id=leave_id,
        status=status,
        db=db,
        lock_reason="LEAVE_WORKFLOW_FINALIZED",
        allowed_statuses={"SANCTIONED", "REJECTED"},
    )