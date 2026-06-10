from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def ensure_identity_active_for_profile_work(profile: dict[str, Any] | None) -> None:
    identity_status = (
        str((profile or {}).get("identity_workflow_status") or "").strip().upper()
    )
    if not identity_status or identity_status == "ACTIVE":
        return

    raise HTTPException(
        status_code=403,
        detail={
            "error_code": "IDENTITY_WORKFLOW_NOT_COMPLETE",
            "message": "Profile editing is available only after the identity workflow is completed.",
            "identity_workflow_status": identity_status,
        },
    )