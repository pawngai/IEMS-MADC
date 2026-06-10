from __future__ import annotations

from fastapi import HTTPException


def require_status(doc: dict, allowed: tuple[str, ...], action: str) -> None:
    status = doc.get("status")
    if status not in allowed:
        if len(allowed) == 1:
            raise HTTPException(400, f"Cannot {action} from {status}. Must be {allowed[0]}.")
        raise HTTPException(400, f"Cannot {action} from {status}")


def require_separation_of_duties(doc: dict, actor: str, *, action: str) -> None:
    if action == "verify" and doc.get("submitted_by") == actor:
        raise HTTPException(403, "Cannot verify a list you submitted (separation of duties)")
    if action == "approve" and (doc.get("submitted_by") == actor or doc.get("verified_by") == actor):
        raise HTTPException(403, "Cannot approve a list you submitted or verified (separation of duties)")
