from __future__ import annotations

from typing import Any

from app_platform.forms.infrastructure.service import FIELD_ALIASES
from app_platform.forms.application.service import validate_form_data


def validate_form_data_hook(
    *,
    data: dict[str, Any],
    workflow_stage: str,
    employment_type: str | None = None,
) -> list[dict[str, Any]]:
    return validate_form_data(
        data=data,
        workflow_stage=workflow_stage,
        employment_type=employment_type,
    )


def get_field_aliases() -> dict[str, tuple[str, ...]]:
    return FIELD_ALIASES
