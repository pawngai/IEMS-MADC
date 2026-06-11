"""Employee-profile contract: media (photo/signature) ownership lookup.

Exists so other contexts (notably ``documents``) can ask "does this employee
own this photo/signature?" without reaching into the employee_profile
collections directly. Keep the surface narrow — only the two URL fields that
correspond to the ``StorageBucket.PHOTO`` and ``StorageBucket.SIGNATURE``
buckets in the documents context are supported.
"""
from __future__ import annotations

_ALLOWED_FIELDS: frozenset[str] = frozenset({"photo_url", "signature_url"})
_LOOKUP_COLLECTIONS: tuple[str, ...] = (
    "employee_profile_read_models",
    "employee_profile_extensions",
)


async def employee_owns_media(
    db,
    *,
    employee_id: str,
    field: str,
    expected_url: str,
    filename: str | None = None,
) -> bool:
    """Return True if any employee_profile read-model row for this
    ``employee_id`` references the given media URL (or bare filename, used as a
    legacy fallback) in ``field``."""
    if field not in _ALLOWED_FIELDS:
        raise ValueError(f"Unsupported media field: {field!r}")
    if not employee_id or db is None:
        return False

    or_clauses: list[dict] = [{field: expected_url}]
    if filename:
        or_clauses.append({field: filename})
    query = {"employee_id": employee_id, "$or": or_clauses}

    for collection_name in _LOOKUP_COLLECTIONS:
        collection = getattr(db, collection_name, None)
        if collection is None or not hasattr(collection, "find_one"):
            continue
        if await collection.find_one(query, {"_id": 1}):
            return True
    return False


__all__ = ["employee_owns_media"]
