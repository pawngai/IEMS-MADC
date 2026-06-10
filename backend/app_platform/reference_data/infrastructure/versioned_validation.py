from __future__ import annotations

from typing import Any

from app_platform.reference_data.contracts.employment_rules import (
    get_available_service_book_parts,
)
from contexts.documents.domain.validation import ALLOWED_DOCUMENT_TYPES
from contexts.rbac.domain.models import Authority, Permission, WorkflowStage


class MasterMetadataValidationError(ValueError):
    pass


EMPLOYMENT_TYPE_RULE_DEFAULTS = {
    "has_pension": True,
    "has_gpf": True,
    "has_leave_account": True,
    "has_increment": True,
    "can_be_promoted": True,
    "can_be_transferred": True,
}


QUALIFICATION_LEVELS = {
    "SECONDARY",
    "HIGHER_SECONDARY",
    "DIPLOMA",
    "BACHELOR",
    "MASTER",
    "DOCTORATE",
    "CERTIFICATION",
}
SERVICE_BOOK_PARTS = set(get_available_service_book_parts("REG"))
PERMISSION_VALUES = {permission.value for permission in Permission}
AUTHORITY_VALUES = {authority.value for authority in Authority}
WORKFLOW_STAGE_VALUES = {stage.value for stage in WorkflowStage}


def _trimmed_string(value: Any) -> str:
    return str(value or "").strip()


def _upper_code(value: Any) -> str:
    return _trimmed_string(value).upper()


def _optional_dict(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    raise MasterMetadataValidationError(f"{field_name} must be an object")


def _optional_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    raise MasterMetadataValidationError(f"{field_name} must be a list")


def _optional_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise MasterMetadataValidationError(f"{field_name} must be a whole number")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise MasterMetadataValidationError(f"{field_name} must be a whole number")
    text = _trimmed_string(value)
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError as exc:
        raise MasterMetadataValidationError(f"{field_name} must be a whole number") from exc
    if not parsed.is_integer():
        raise MasterMetadataValidationError(f"{field_name} must be a whole number")
    return int(parsed)


def _optional_float(value: Any, field_name: str) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise MasterMetadataValidationError(f"{field_name} must be a number")
    if isinstance(value, (int, float)):
        return float(value)
    text = _trimmed_string(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise MasterMetadataValidationError(f"{field_name} must be a number") from exc


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize_membership_list(
    value: Any,
    *,
    field_name: str,
    allowed_values: set[str],
    uppercase: bool = True,
) -> list[str]:
    raw_values = _optional_list(value, field_name)
    normalized: list[str] = []
    for item in raw_values:
        normalized_item = _upper_code(item) if uppercase else _trimmed_string(item)
        if not normalized_item:
            continue
        if normalized_item not in allowed_values:
            raise MasterMetadataValidationError(
                f"Unsupported value '{normalized_item}' for {field_name}"
            )
        normalized.append(normalized_item)
    return _dedupe_preserve_order(normalized)


def validate_and_normalize_master_metadata(
    master_type: str,
    code: str,
    metadata: dict[str, Any] | None,
    *,
    current_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_code = _upper_code(code)
    base_metadata = _optional_dict(current_metadata, "current_metadata")
    incoming_metadata = _optional_dict(metadata, "metadata")
    merged_metadata = {**base_metadata, **incoming_metadata}
    normalized = dict(merged_metadata)

    if master_type == "employment_type":
        base_rules = _optional_dict(base_metadata.get("rules"), "rules")
        incoming_rules = _optional_dict(incoming_metadata.get("rules"), "rules")
        merged_rules = {**base_rules, **incoming_rules}
        normalized["type_code"] = normalized_code
        normalized["rules"] = {
            key: bool(merged_rules.get(key, default_value))
            for key, default_value in EMPLOYMENT_TYPE_RULE_DEFAULTS.items()
        }
        return normalized

    if master_type == "pay_level":
        pay_band = _trimmed_string(merged_metadata.get("pay_band"))
        basic_min = _optional_int(merged_metadata.get("basic_min"), "Basic Min")
        basic_max = _optional_int(merged_metadata.get("basic_max"), "Basic Max")
        annual_increment_rate = _optional_float(
            merged_metadata.get("annual_increment_rate"),
            "Annual Increment Rate",
        )
        grade_pay = _optional_int(merged_metadata.get("grade_pay"), "Grade Pay")
        if not pay_band or basic_min is None or basic_max is None:
            raise MasterMetadataValidationError(
                "Pay Band, Basic Min, and Basic Max are required"
            )
        if basic_max < basic_min:
            raise MasterMetadataValidationError(
                "Basic Max must be greater than or equal to Basic Min"
            )
        if annual_increment_rate is not None and annual_increment_rate < 0:
            raise MasterMetadataValidationError(
                "Annual Increment Rate cannot be negative"
            )
        if grade_pay is not None and grade_pay < 0:
            raise MasterMetadataValidationError("Grade Pay cannot be negative")
        normalized.update(
            {
                "pay_band": pay_band,
                "basic_min": basic_min,
                "basic_max": basic_max,
                "annual_increment_rate": annual_increment_rate
                if annual_increment_rate is not None
                else 3.0,
            }
        )
        if grade_pay is None:
            normalized.pop("grade_pay", None)
        else:
            normalized["grade_pay"] = grade_pay
        return normalized

    if master_type == "service_event_type":
        event_code = _upper_code(merged_metadata.get("event_code"))
        service_book_part = _trimmed_string(merged_metadata.get("service_book_part"))
        if not event_code or not service_book_part:
            raise MasterMetadataValidationError(
                "Event code and Service Book Part are required"
            )
        if service_book_part not in SERVICE_BOOK_PARTS:
            raise MasterMetadataValidationError(
                f"Unsupported value '{service_book_part}' for service_book_part"
            )
        normalized.update(
            {
                "event_code": event_code,
                "service_book_part": service_book_part,
                "requires_order_number": bool(
                    merged_metadata.get("requires_order_number", True)
                ),
                "affects_pay": bool(merged_metadata.get("affects_pay", False)),
                "affects_posting": bool(
                    merged_metadata.get("affects_posting", False)
                ),
            }
        )
        return normalized

    if master_type == "leave_type":
        max_days_per_year = _optional_int(
            merged_metadata.get("max_days_per_year"),
            "Max Days Per Year",
        )
        min_days_per_spell = _optional_int(
            merged_metadata.get("min_days_per_spell"),
            "Min Days Per Spell",
        )
        max_days_per_spell = _optional_int(
            merged_metadata.get("max_days_per_spell"),
            "Max Days Per Spell",
        )
        max_days_lifetime = _optional_int(
            merged_metadata.get("max_days_lifetime"),
            "Max Days Lifetime",
        )
        if max_days_per_year is not None and max_days_per_year < 0:
            raise MasterMetadataValidationError(
                "Max Days Per Year cannot be negative"
            )
        if min_days_per_spell is not None and min_days_per_spell < 0:
            raise MasterMetadataValidationError(
                "Min Days Per Spell cannot be negative"
            )
        if max_days_per_spell is not None and max_days_per_spell < 0:
            raise MasterMetadataValidationError(
                "Max Days Per Spell cannot be negative"
            )
        if max_days_lifetime is not None and max_days_lifetime < 0:
            raise MasterMetadataValidationError(
                "Max Days Lifetime cannot be negative"
            )
        if (
            min_days_per_spell is not None
            and max_days_per_spell is not None
            and max_days_per_spell < min_days_per_spell
        ):
            raise MasterMetadataValidationError(
                "Max Days Per Spell must be greater than or equal to Min Days Per Spell"
            )
        normalized["leave_code"] = normalized_code
        normalized["is_encashable"] = bool(merged_metadata.get("is_encashable", False))
        normalized["is_accumulative"] = bool(
            merged_metadata.get("is_accumulative", False)
        )
        normalized["applicable_employment_types"] = _dedupe_preserve_order(
            [
                value
                for value in (_upper_code(item) for item in _optional_list(merged_metadata.get("applicable_employment_types"), "Applicable Employment Types"))
                if value
            ]
        )
        if max_days_per_year is None:
            normalized.pop("max_days_per_year", None)
        else:
            normalized["max_days_per_year"] = max_days_per_year
        if min_days_per_spell is None:
            normalized.pop("min_days_per_spell", None)
        else:
            normalized["min_days_per_spell"] = min_days_per_spell
        if max_days_per_spell is None:
            normalized.pop("max_days_per_spell", None)
        else:
            normalized["max_days_per_spell"] = max_days_per_spell
        if max_days_lifetime is None:
            normalized.pop("max_days_lifetime", None)
        else:
            normalized["max_days_lifetime"] = max_days_lifetime
        return normalized

    if master_type == "department":
        parent_department_code = _upper_code(merged_metadata.get("parent_department_code"))
        if parent_department_code and parent_department_code == normalized_code:
            raise MasterMetadataValidationError(
                "Parent Department cannot be the same as the record code"
            )
        if parent_department_code:
            normalized["parent_department_code"] = parent_department_code
        else:
            normalized.pop("parent_department_code", None)
        normalized.pop("ministry_code", None)
        normalized.pop("department_type", None)
        return normalized

    if master_type == "designation":
        pay_level_code = _upper_code(merged_metadata.get("pay_level_code"))
        service_group_code = _upper_code(merged_metadata.get("service_group_code"))
        if not pay_level_code or not service_group_code:
            raise MasterMetadataValidationError(
                "Pay Level and Service Group are required"
            )
        normalized.update(
            {
                "pay_level_code": pay_level_code,
                "service_group_code": service_group_code,
                "is_gazetted": bool(merged_metadata.get("is_gazetted", False)),
                "is_supervisory": bool(
                    merged_metadata.get("is_supervisory", False)
                ),
            }
        )
        return normalized

    if master_type == "caste_category":
        reservation_percentage = _optional_float(
            merged_metadata.get("reservation_percentage"),
            "Reservation Percentage",
        )
        if reservation_percentage is None:
            reservation_percentage = 0.0
        if reservation_percentage < 0 or reservation_percentage > 100:
            raise MasterMetadataValidationError(
                "Reservation Percentage must be between 0 and 100"
            )
        normalized["category_code"] = normalized_code
        normalized["reservation_percentage"] = reservation_percentage
        return normalized

    if master_type == "service_group":
        group_code = _upper_code(merged_metadata.get("group_code"))
        if not group_code:
            raise MasterMetadataValidationError("Group Code is required")
        normalized["group_code"] = group_code
        normalized["is_gazetted"] = bool(merged_metadata.get("is_gazetted", False))
        return normalized

    if master_type == "document_type":
        normalized["supported_content_types"] = _normalize_membership_list(
            merged_metadata.get("supported_content_types"),
            field_name="supported_content_types",
            allowed_values=set(ALLOWED_DOCUMENT_TYPES),
            uppercase=False,
        )
        return normalized

    if master_type == "qualification":
        level = _upper_code(merged_metadata.get("level"))
        if not level:
            raise MasterMetadataValidationError("Qualification level is required")
        if level not in QUALIFICATION_LEVELS:
            raise MasterMetadataValidationError(
                f"Unsupported value '{level}' for level"
            )
        discipline = _trimmed_string(merged_metadata.get("discipline"))
        normalized["level"] = level
        if discipline:
            normalized["discipline"] = discipline
        else:
            normalized.pop("discipline", None)
        return normalized

    if master_type == "role":
        permissions = _normalize_membership_list(
            merged_metadata.get("permissions"),
            field_name="permissions",
            allowed_values=PERMISSION_VALUES,
        )
        if not permissions:
            raise MasterMetadataValidationError("Select at least one permission")
        normalized["permissions"] = permissions
        return normalized

    if master_type == "workflow_stage":
        next_stages = _normalize_membership_list(
            merged_metadata.get("next_stages"),
            field_name="next_stages",
            allowed_values=WORKFLOW_STAGE_VALUES,
        )
        required_authority = _normalize_membership_list(
            merged_metadata.get("required_authority"),
            field_name="required_authority",
            allowed_values=AUTHORITY_VALUES,
        )
        if normalized_code and normalized_code in next_stages:
            raise MasterMetadataValidationError(
                "Next Stages cannot include the current record code"
            )
        normalized["next_stages"] = next_stages
        normalized["required_authority"] = required_authority
        normalized["can_edit"] = bool(merged_metadata.get("can_edit", False))
        return normalized

    return normalized