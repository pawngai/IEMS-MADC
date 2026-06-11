from __future__ import annotations

from typing import Optional

from fastapi import HTTPException


CREATE_STRICT_REQUIRED_FORM_FIELDS = {
    "full_name",
    "gender",
    "date_of_birth",
    "employment_type",
    "date_of_initial_engagement",
    "department_code",
}

CREATE_CONDITIONAL_REQUIRED_FORM_FIELDS = {
    "CONTRACTUAL": {"designation_code"},
    "DAILY_WAGE": {"designation_code"},
    "DEPUTATION": {"designation_code"},
    "REEMPLOYED": {"designation_code"},
    "OUTSOURCED": {"outsourcing_agency", "designation_code"},
}

def flatten_employee_record_for_forms(profile: dict) -> dict:
    flattened = dict(profile or {})
    flattened.update((profile or {}).get("contact") or {})
    flattened.update((profile or {}).get("identifiers") or {})
    return flattened


def _is_error_field_actionable(
    field_id: str,
    payload: dict,
    field_aliases: dict[str, tuple[str, ...]] | dict[str, list[str]] | None,
) -> bool:
    if field_id in payload:
        return True
    alias_candidates = (field_aliases or {}).get(field_id, (field_id,))
    return any(candidate in payload for candidate in alias_candidates)


def strict_required_form_fields_for_create(employment_type: Optional[str]) -> set[str]:
    normalized = str(employment_type or "").strip().upper()
    conditional = CREATE_CONDITIONAL_REQUIRED_FORM_FIELDS.get(normalized, set())
    return set(CREATE_STRICT_REQUIRED_FORM_FIELDS) | set(conditional)


def filtered_form_errors(
    errors: list[dict],
    payload: dict,
    *,
    required_fields_always_actionable: Optional[set[str]] = None,
    field_aliases: dict[str, tuple[str, ...]] | dict[str, list[str]] | None = None,
) -> list[dict]:
    required_fields_always_actionable = required_fields_always_actionable or set()

    def _is_actionable(error: dict) -> bool:
        field_id = str(error.get("field_id") or "")
        if not field_id:
            return False
        if _is_error_field_actionable(field_id, payload, field_aliases):
            return True
        if (
            str(error.get("error_type") or "").lower() == "required"
            and field_id in required_fields_always_actionable
        ):
            return True
        return False

    return [error for error in (errors or []) if _is_actionable(error)]


def _raise_form_validation_failed(errors: list[dict]) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "FORM_VALIDATION_FAILED",
            "message": "Profile data failed dynamic forms validation",
            "errors": errors,
        },
    )


def raise_form_validation_failed(errors: list[dict]) -> None:
    _raise_form_validation_failed(errors)
