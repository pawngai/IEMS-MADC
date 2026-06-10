"""Documents domain — file validation rules and ownership checks."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# ── Allowed file types & size limits ────────────────────────────────

ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

ALLOWED_DOCUMENT_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

MAX_FILE_SIZE: int = 5 * 1024 * 1024
MAX_DOCUMENT_SIZE: int = 10 * 1024 * 1024

ALLOWED_DOCUMENT_ENTITY_TYPES: set[str] = {
    "CHANGE_REQUEST",
    "LEAVE",
    "MASTER_DATA",
    "SERVICE_BOOK",
    "SERVICE_RECORD",
    "SERVICE_EVENT",
}

DOCUMENT_TYPE_RECORDS: tuple[dict[str, str], ...] = (
    {
        "code": "ORDER",
        "name": "Order",
        "description": "Official order document",
    },
    {
        "code": "NOTIFICATION",
        "name": "Notification",
        "description": "Official notification document",
    },
    {
        "code": "MEMORANDUM",
        "name": "Memorandum",
        "description": "Office memorandum or memo",
    },
    {
        "code": "CERTIFICATE",
        "name": "Certificate",
        "description": "Certificate or attestation document",
    },
    {
        "code": "REPORT",
        "name": "Report",
        "description": "Report or statement document",
    },
)

ALLOWED_DOCUMENT_TYPE_CODES: set[str] = {record["code"] for record in DOCUMENT_TYPE_RECORDS}

_DOCUMENT_SOURCE_CONTEXT_PATTERN = re.compile(r"[a-z0-9]+(?:[._][a-z0-9]+)*")
_DOCUMENT_CATEGORY_PATTERN = re.compile(r"[A-Z0-9]+(?:_[A-Z0-9]+)*")
_DOCUMENT_TAG_PATTERN = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")

MAX_DOCUMENT_TAGS: int = 16
MAX_DOCUMENT_TAG_LENGTH: int = 32

_MAGIC_BYTES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/jpg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
    "application/pdf": [b"%PDF"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        b"PK\x03\x04"
    ],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        b"PK\x03\x04"
    ],
    "application/msword": [b"\xd0\xcf\x11\xe0"],
    "application/vnd.ms-excel": [b"\xd0\xcf\x11\xe0"],
}


# ── Pure validation functions (raise ValueError, not HTTPException) ─

def validate_magic_bytes(contents: bytes, claimed_type: str) -> None:
    """Raise ValueError if the file header doesn't match *claimed_type*."""
    signatures = _MAGIC_BYTES.get(claimed_type)
    if signatures is None:
        raise ValueError(f"Cannot verify file type '{claimed_type}'")

    for sig in signatures:
        if contents[: len(sig)] == sig:
            if claimed_type == "image/webp" and contents[8:12] != b"WEBP":
                break
            return

    raise ValueError(
        f"File content does not match declared type '{claimed_type}'. "
        "Ensure the file is not corrupted or renamed."
    )


def validate_safe_filename(filename: str, base_dir: Path) -> Path:
    """Raise ValueError if *filename* contains traversal attacks."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("Invalid filename: path traversal attempts are not allowed")

    file_path = (base_dir / filename).resolve()
    try:
        file_path.relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError("Invalid filename: file must be within the documents directory")

    return file_path


def validate_image_content_type(content_type: str | None) -> None:
    """Raise ValueError if *content_type* is not an allowed image type."""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            f"File type '{content_type}' not allowed. Allowed types: JPEG, PNG, WebP"
        )


def validate_document_content_type(content_type: str | None) -> None:
    """Raise ValueError if *content_type* is not an allowed document type."""
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError(
            f"File type '{content_type}' not allowed. "
            "Allowed: PDF, JPEG, PNG, DOC, DOCX, XLS, XLSX"
        )


def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE) -> None:
    """Raise ValueError if *file_size* exceeds *max_size*."""
    if file_size > max_size:
        raise ValueError(
            f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum "
            f"({max_size / 1024 / 1024}MB)"
        )


def normalize_document_entity_type(entity_type: str | None) -> str | None:
    if entity_type is None:
        return None

    normalized = str(entity_type).strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized:
        return None
    if normalized not in ALLOWED_DOCUMENT_ENTITY_TYPES:
        allowed_values = ", ".join(sorted(ALLOWED_DOCUMENT_ENTITY_TYPES))
        raise ValueError(
            f"entity_type '{entity_type}' not allowed. Allowed types: {allowed_values}"
        )
    return normalized


def normalize_document_type(document_type: str | None) -> str | None:
    if document_type is None:
        return None

    normalized = str(document_type).strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized:
        return None
    if normalized not in ALLOWED_DOCUMENT_TYPE_CODES:
        allowed_values = ", ".join(sorted(ALLOWED_DOCUMENT_TYPE_CODES))
        raise ValueError(
            f"document_type '{document_type}' not allowed. Allowed types: {allowed_values}"
        )
    return normalized


def normalize_document_source_context(source_context: str | None) -> str | None:
    if source_context is None:
        return None

    normalized = str(source_context).strip().lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        return None
    if _DOCUMENT_SOURCE_CONTEXT_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            "source_context must contain only lowercase letters, numbers, dots, and underscores"
        )
    return normalized


def normalize_document_category(category: str | None) -> str | None:
    if category is None:
        return None

    normalized = str(category).strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized:
        return None
    if _DOCUMENT_CATEGORY_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            "category must contain only letters, numbers, and underscores"
        )
    return normalized


def normalize_tags(tags: Any) -> list[str] | None:
    """Normalize a list of free-form tags. Accepts list/tuple/None; rejects
    other shapes. Tags are lowercased, space → hyphen, deduplicated, sorted,
    and validated against length + charset limits."""
    if tags is None:
        return None
    if isinstance(tags, str):
        # Single string is a common caller mistake — treat as a one-element list.
        tags = [tags]
    if not isinstance(tags, (list, tuple)):
        raise ValueError("tags must be a list of strings")

    seen: set[str] = set()
    normalized: list[str] = []
    for raw in tags:
        if raw is None:
            continue
        text = str(raw).strip().lower().replace(" ", "-")
        if not text:
            continue
        if len(text) > MAX_DOCUMENT_TAG_LENGTH:
            raise ValueError(
                f"tag '{raw}' exceeds the {MAX_DOCUMENT_TAG_LENGTH}-character limit"
            )
        if _DOCUMENT_TAG_PATTERN.fullmatch(text) is None:
            raise ValueError(
                f"tag '{raw}' must contain only lowercase letters, numbers, hyphens, and underscores"
            )
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text)

    if len(normalized) > MAX_DOCUMENT_TAGS:
        raise ValueError(f"a document may have at most {MAX_DOCUMENT_TAGS} tags")
    normalized.sort()
    return normalized


# ── Content-type helpers ────────────────────────────────────────────

_IMAGE_EXTENSIONS: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

_DOCUMENT_EXTENSIONS: dict[str, str] = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# Canonical extension per validated MIME type. Used to derive a safe extension
# for stored filenames regardless of what the uploader put in the original
# filename. Keep aligned with ``_IMAGE_EXTENSIONS`` and ``_DOCUMENT_EXTENSIONS``.
_CONTENT_TYPE_TO_CANONICAL_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}


def content_type_for_image(filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    return _IMAGE_EXTENSIONS.get(ext, "application/octet-stream")


def content_type_for_document(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _DOCUMENT_EXTENSIONS.get(ext, "application/octet-stream")


def extension_for_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return _CONTENT_TYPE_TO_CANONICAL_EXT.get(content_type.strip().lower())


# ── Ownership checks ───────────────────────────────────────────────

def is_document_locked(metadata: dict[str, Any] | None) -> bool:
    data = metadata or {}
    return bool(data.get("locked_at") or data.get("is_locked") or data.get("lock_reason"))


def is_legal_hold_active(metadata: dict[str, Any] | None) -> bool:
    """Return True if the document is under legal hold. Legal hold is a
    separate, admin-only protection that is unbounded in time — distinct
    from the time-bounded approval lock that ``is_document_locked`` reports."""
    data = metadata or {}
    return bool(data.get("legal_hold"))


def is_document_protected_from_mutation(metadata: dict[str, Any] | None) -> bool:
    """Combined predicate: either an approval lock or an active legal hold
    protects the document from deletion / supersede."""
    return is_document_locked(metadata) or is_legal_hold_active(metadata)


def is_document_owner(metadata: dict[str, Any] | None, current_user: dict[str, Any]) -> bool:
    data = metadata or {}
    req_eid = str(current_user.get("employee_id") or "")
    req_ecode = str(current_user.get("employee_code") or "")
    req_uid = str(current_user.get("sub") or current_user.get("id") or "")
    stored_eid = str(data.get("uploaded_employee_id") or "")
    stored_ecode = str(data.get("uploaded_employee_code") or "")
    stored_uid = str(data.get("uploaded_by_user_id") or "")

    if req_eid and stored_eid:
        return req_eid == stored_eid
    if req_ecode and stored_ecode:
        return req_ecode == stored_ecode
    return bool(req_uid and stored_uid and req_uid == stored_uid)


def extract_filename_from_attachment(attachment: Any) -> str:
    if not isinstance(attachment, dict):
        return ""
    direct = str(attachment.get("filename") or "").strip()
    if direct:
        return direct
    url = str(attachment.get("url") or "").strip()
    if not url:
        return ""
    return url.split("/")[-1].split("?")[0].strip()
