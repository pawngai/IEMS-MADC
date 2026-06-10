from __future__ import annotations

from fastapi import HTTPException


def is_regular_employee(identity: dict | None) -> bool:
    employment_type = str(
        (identity or {}).get("current_employment_type_code")
        or (identity or {}).get("employment_type")
        or (identity or {}).get("employment_type_code")
        or ""
    ).strip().upper()
    return employment_type in {"REG", "REGULAR"}


def require_regular_opening(identity: dict | None) -> None:
    if is_regular_employee(identity):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error_code": "SERVICE_BOOK_OPENING_NOT_APPLICABLE",
            "message": "Service Book Opening is only available for REGULAR employees.",
            "required_employment_type": "REGULAR",
        },
    )
