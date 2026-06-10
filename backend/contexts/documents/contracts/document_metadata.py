from __future__ import annotations

from fastapi import HTTPException


def _subject_keys_from_current_user(current_user: dict) -> tuple[str, str | None]:
    """Pull the subject identifiers off the authenticated principal. Returns
    ``(employee_id, employee_code_or_None)`` and raises 403 if neither is set —
    callers should never reach the subject-document path without an identity."""
    employee_id = str(current_user.get("employee_id") or "").strip()
    employee_code = str(current_user.get("employee_code") or "").strip() or None
    if not employee_id and not employee_code:
        raise HTTPException(
            status_code=403,
            detail="Subject document access requires an employee identity on the request principal",
        )
    return employee_id, employee_code


async def get_accessible_document_metadata(filename: str, *, current_user: dict, db=None) -> dict:
    from contexts.documents.application.service import (
        get_document_metadata as _get_document_metadata,
    )

    result = await _get_document_metadata(filename, current_user=current_user, db=db)
    return dict(result.get("item") or {})


async def list_subject_documents_for_employee(
    *,
    employee_id: str,
    employee_code: str | None = None,
    query: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    source_context: str | None = None,
    is_locked: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db=None,
) -> dict:
    from contexts.documents.application.service import (
        list_subject_documents as _list_subject_documents,
    )

    return await _list_subject_documents(
        employee_id=employee_id,
        employee_code=employee_code,
        query=query,
        entity_type=entity_type,
        entity_id=entity_id,
        document_type=document_type,
        category=category,
        source_context=source_context,
        is_locked=is_locked,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
        db=db,
    )


async def download_subject_document_for_employee(
    filename: str,
    *,
    employee_id: str,
    employee_code: str | None = None,
    db=None,
):
    from contexts.documents.application.service import (
        download_subject_document as _download_subject_document,
    )

    return await _download_subject_document(
        filename,
        employee_id=employee_id,
        employee_code=employee_code,
        db=db,
    )


async def get_subject_document_for_employee(
    filename: str,
    *,
    employee_id: str,
    employee_code: str | None = None,
    db=None,
):
    from contexts.documents.application.service import (
        get_subject_document as _get_subject_document,
    )

    return await _get_subject_document(
        filename,
        employee_id=employee_id,
        employee_code=employee_code,
        db=db,
    )


async def get_subject_document_for_current_user(
    filename: str,
    *,
    current_user: dict,
    db=None,
):
    """Same as :func:`get_subject_document_for_employee` but pulls the subject
    identity off ``current_user`` so callers can't accidentally fetch another
    employee's document."""
    employee_id, employee_code = _subject_keys_from_current_user(current_user)
    return await get_subject_document_for_employee(
        filename,
        employee_id=employee_id,
        employee_code=employee_code,
        db=db,
    )


async def download_subject_document_for_current_user(
    filename: str,
    *,
    current_user: dict,
    db=None,
):
    """Same as :func:`download_subject_document_for_employee` but pulls the
    subject identity off ``current_user``."""
    employee_id, employee_code = _subject_keys_from_current_user(current_user)
    return await download_subject_document_for_employee(
        filename,
        employee_id=employee_id,
        employee_code=employee_code,
        db=db,
    )


__all__ = [
    "download_subject_document_for_current_user",
    "download_subject_document_for_employee",
    "get_accessible_document_metadata",
    "get_subject_document_for_current_user",
    "get_subject_document_for_employee",
    "list_subject_documents_for_employee",
]