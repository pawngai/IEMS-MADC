from __future__ import annotations

from typing import Any


def get_fields_for_employment_type(
    employment_type: str,
    *,
    common_fields: list[dict[str, Any]],
    employment_type_fields: dict[Any, list[dict[str, Any]]],
    employment_type_enum,
) -> list[dict[str, Any]]:
    all_fields = common_fields.copy()

    try:
        emp_type = employment_type_enum(employment_type)
        if emp_type in employment_type_fields:
            all_fields.extend(employment_type_fields[emp_type])
    except ValueError:
        pass

    return all_fields


def get_allowed_field_ids(
    employment_type: str,
    *,
    common_fields: list[dict[str, Any]],
    employment_type_fields: dict[Any, list[dict[str, Any]]],
    employment_type_enum,
) -> list[str]:
    fields = get_fields_for_employment_type(
        employment_type,
        common_fields=common_fields,
        employment_type_fields=employment_type_fields,
        employment_type_enum=employment_type_enum,
    )
    return [field["field_id"] for field in fields]


def validate_submission(
    employment_type: str,
    data: dict[str, Any],
    *,
    common_fields: list[dict[str, Any]],
    employment_type_fields: dict[Any, list[dict[str, Any]]],
    employment_type_enum,
    rejected_fields: list[str],
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    allowed_fields = get_allowed_field_ids(
        employment_type,
        common_fields=common_fields,
        employment_type_fields=employment_type_fields,
        employment_type_enum=employment_type_enum,
    )

    for field in rejected_fields:
        if field in data and data[field] is not None:
            errors.append(
                {
                    "field": field,
                    "error": f"Field '{field}' is not allowed in Employee Profile. It belongs to Service Book.",
                }
            )

    for field_id in data.keys():
        if field_id in allowed_fields or field_id in {"id", "created_at", "updated_at"}:
            continue
        if field_id in rejected_fields:
            continue
        for emp_type, fields in employment_type_fields.items():
            if emp_type.value == employment_type:
                continue
            if any(field["field_id"] == field_id for field in fields):
                errors.append(
                    {
                        "field": field_id,
                        "error": f"Field '{field_id}' is not valid for employment type '{employment_type}'. It belongs to '{emp_type.value}'.",
                    }
                )
                break

    fields = get_fields_for_employment_type(
        employment_type,
        common_fields=common_fields,
        employment_type_fields=employment_type_fields,
        employment_type_enum=employment_type_enum,
    )
    for field in fields:
        if not field.get("required", False):
            continue
        field_id = field["field_id"]
        if field_id in data and data.get(field_id) not in [None, "", []]:
            continue
        if not field.get("auto_generated", False):
            errors.append(
                {
                    "field": field_id,
                    "error": f"Required field '{field['label']}' is missing.",
                }
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


__all__ = [
    "get_allowed_field_ids",
    "get_fields_for_employment_type",
    "validate_submission",
]