from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict


REVISION_COLLECTION = "service_book_part_revisions"


def canonical_json(value: Any) -> str:
    def _default(obj: Any) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_default,
    )


def compute_revision_hash(
    part_code: str,
    employee_id: str,
    sequence: int,
    prev_hash: str,
    payload: Dict[str, Any],
) -> str:
    source = f"{part_code}|{employee_id}|{sequence}|{prev_hash}|{canonical_json(payload)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


async def append_revision(
    db,
    *,
    part_code: str,
    employee_id: str,
    payload: Dict[str, Any],
    actor_user_id: str,
    session=None,
) -> Dict[str, Any]:
    find_kwargs = {"sort": [("sequence", -1)]}
    if session is not None:
        find_kwargs["session"] = session
    latest = await db[REVISION_COLLECTION].find_one(
        {"employee_id": employee_id, "part": part_code},
        {"_id": 0, "sequence": 1, "hash": 1},
        **find_kwargs,
    )

    prev_sequence = int((latest or {}).get("sequence", 0))
    prev_hash = (latest or {}).get("hash", "")
    sequence = prev_sequence + 1
    now = datetime.now(timezone.utc).isoformat()

    revision = {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "part": part_code,
        "sequence": sequence,
        "payload": payload,
        "prev_hash": prev_hash,
        "hash": compute_revision_hash(part_code, employee_id, sequence, prev_hash, payload),
        "created_at": now,
        "created_by": actor_user_id,
    }
    if session is None:
        await db[REVISION_COLLECTION].insert_one(revision)
    else:
        await db[REVISION_COLLECTION].insert_one(revision, session=session)
    return revision