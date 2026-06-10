from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


from contexts.service_book.records.schemas.service_event_types import CPC_OPTIONS, PayCommission, ServiceEventCategory


CPC_CHANGE_FIXATION_EXTERNAL_TYPE = "CPC_CHANGE_FIXATION"


MANDATORY_ORDER_METADATA_BY_CATEGORY: dict[ServiceEventCategory, tuple[str, ...]] = {}

GLOBAL_MANDATORY_ORDER_METADATA: tuple[str, ...] = ("order_no", "order_date")


def _normalize_category_value(raw: Any) -> str:
    normalized = str(raw or ServiceEventCategory.GENERIC.value).strip().upper()
    if normalized == CPC_CHANGE_FIXATION_EXTERNAL_TYPE:
        return ServiceEventCategory.CPC_PAY_FIXATION.value
    return normalized or ServiceEventCategory.GENERIC.value


def _normalize_pay_commission(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    return normalized if normalized in {item.value for item in PayCommission} else ""


def _clean_nested_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    cleaned: dict[str, Any] = {}
    for key, raw_item in value.items():
        if raw_item is None:
            continue
        if isinstance(raw_item, dict):
            nested = _clean_nested_payload(raw_item)
            if nested:
                cleaned[str(key)] = nested
            continue
        if isinstance(raw_item, str):
            normalized = raw_item.strip()
            if normalized:
                cleaned[str(key)] = normalized
            continue
        cleaned[str(key)] = raw_item

    return cleaned


def _build_cpc_fixation_section(payload: dict[str, Any], field_map: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    section: dict[str, Any] = {}
    for source_key, target_key in field_map:
        raw_value = payload.get(source_key)
        if raw_value is None:
            continue
        if isinstance(raw_value, str):
            normalized = raw_value.strip()
            if normalized:
                section[target_key] = normalized
            continue
        section[target_key] = raw_value
    return section


def _legacy_cpc_fixation_sections(payload: dict[str, Any], from_cpc: str, to_cpc: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    pre_field_map = {
        PayCommission.CPC_4.value: (("from_pay_scale", "pay_scale"), ("from_basic_pay", "basic_pay")),
        PayCommission.CPC_5.value: (("from_pay_scale", "pay_scale"), ("from_basic_pay", "basic_pay")),
        PayCommission.CPC_6.value: (("from_pay_band", "pay_band"), ("from_grade_pay", "grade_pay"), ("from_basic_pay", "basic_pay")),
        PayCommission.CPC_7.value: (("from_pay_level", "pay_level"), ("from_pay_cell_index", "pay_cell_index"), ("from_basic_pay", "basic_pay")),
    }
    fitment_field_map = {
        PayCommission.CPC_4.value: (("pay_scale", "pay_scale"),),
        PayCommission.CPC_5.value: (("pay_scale", "pay_scale"),),
        PayCommission.CPC_6.value: (("pay_band", "pay_band"), ("grade_pay", "grade_pay")),
        PayCommission.CPC_7.value: (("pay_level", "pay_level"), ("pay_cell_index", "pay_cell_index")),
    }
    post_field_map = {
        PayCommission.CPC_4.value: (("pay_scale", "pay_scale"), ("to_basic_pay", "basic_pay")),
        PayCommission.CPC_5.value: (("pay_scale", "pay_scale"), ("to_basic_pay", "basic_pay")),
        PayCommission.CPC_6.value: (("pay_band", "pay_band"), ("grade_pay", "grade_pay"), ("to_basic_pay", "basic_pay")),
        PayCommission.CPC_7.value: (("pay_level", "pay_level"), ("pay_cell_index", "pay_cell_index"), ("to_basic_pay", "basic_pay")),
    }

    pre = _build_cpc_fixation_section(payload, pre_field_map.get(from_cpc, ()))
    fitment = _build_cpc_fixation_section(payload, fitment_field_map.get(to_cpc, ()))
    post = _build_cpc_fixation_section(payload, post_field_map.get(to_cpc, ()))
    return pre, fitment, post


def _normalize_cpc_fixation_payload(raw: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    from_cpc = _normalize_pay_commission(raw.get("from_cpc") or payload.get("from_cpc"))
    to_cpc = _normalize_pay_commission(raw.get("to_cpc") or payload.get("to_cpc") or payload.get("cpc"))

    legacy_pre, legacy_fitment, legacy_post = _legacy_cpc_fixation_sections(payload, from_cpc, to_cpc)
    nested_pre = _clean_nested_payload(raw.get("pre_revised_pay") or payload.get("pre_revised_pay"))
    nested_fitment = _clean_nested_payload(raw.get("fitment") or payload.get("fitment"))
    nested_post = _clean_nested_payload(raw.get("post_revised_pay") or payload.get("post_revised_pay"))
    nested_option = _clean_nested_payload(raw.get("option") or payload.get("option"))

    normalized_payload = {
        "effective_date": str(
            raw.get("effective_date")
            or payload.get("effective_date")
            or payload.get("fixation_date")
            or ""
        ).strip(),
        "order_no": str(raw.get("order_no") or payload.get("order_no") or "").strip(),
        "order_date": str(raw.get("order_date") or payload.get("order_date") or "").strip(),
        "from_cpc": from_cpc,
        "to_cpc": to_cpc,
        "pre_revised_pay": {**legacy_pre, **nested_pre},
        "fitment": {**legacy_fitment, **nested_fitment},
        "post_revised_pay": {**legacy_post, **nested_post},
        "option": nested_option,
        "remarks": str(raw.get("remarks") or payload.get("remarks") or "").strip(),
    }

    return normalized_payload


def _validate_cpc_fixation_payload(payload: dict[str, Any]) -> None:
    effective_date = str(payload.get("effective_date") or "").strip()
    if not effective_date:
        raise ValueError("payload missing required keys for CPC_PAY_FIXATION: effective_date")
    date.fromisoformat(effective_date)

    from_cpc = _normalize_pay_commission(payload.get("from_cpc"))
    to_cpc = _normalize_pay_commission(payload.get("to_cpc"))
    if not from_cpc or not to_cpc:
        raise ValueError("payload.from_cpc and payload.to_cpc are required for CPC_PAY_FIXATION")

    for key in ("pre_revised_pay", "fitment", "post_revised_pay", "option"):
        value = payload.get(key, {})
        if not isinstance(value, dict):
            raise ValueError(f"payload.{key} must be an object")

    pre_revised_pay = payload.get("pre_revised_pay") or {}
    post_revised_pay = payload.get("post_revised_pay") or {}
    fitment = payload.get("fitment") or {}

    if not str(pre_revised_pay.get("basic_pay") or "").strip():
        raise ValueError("payload.pre_revised_pay.basic_pay is required for CPC_PAY_FIXATION")
    if not str(post_revised_pay.get("basic_pay") or "").strip():
        raise ValueError("payload.post_revised_pay.basic_pay is required for CPC_PAY_FIXATION")

    target_required_fields = {
        PayCommission.CPC_4.value: ("pay_scale",),
        PayCommission.CPC_5.value: ("pay_scale",),
        PayCommission.CPC_6.value: ("pay_band", "grade_pay"),
        PayCommission.CPC_7.value: ("pay_level", "pay_cell_index"),
    }.get(to_cpc, ())
    missing_target = [
        key
        for key in target_required_fields
        if not str(post_revised_pay.get(key) or fitment.get(key) or "").strip()
    ]
    if missing_target:
        raise ValueError(
            "payload missing post revised pay keys for "
            f"CPC_PAY_FIXATION/{to_cpc}: {', '.join(sorted(missing_target))}"
        )


from contexts.service_book.records.schemas.service_event_form_schema import (
    CANONICAL_CATEGORY_OPTIONS,
    CPC_FIELD_DEFINITIONS,
    CPC_PAYLOAD_KEYS_BY_CATEGORY,
    EVENT_CATEGORY_TO_PART_CODE,
    FIELD_DEFINITIONS,
    REQUIRED_PAYLOAD_KEYS_BY_CATEGORY,
    get_service_event_form_schema,
)


class CanonicalServiceEventInput(BaseModel):
    employee_id: str = Field(min_length=1)
    category: ServiceEventCategory = Field(default=ServiceEventCategory.GENERIC)
    payload: dict[str, Any] = Field(default_factory=dict)
    effective_from: str | None = None
    effective_to: str | None = None
    part_code: str | None = None

    @field_validator("employee_id")
    @classmethod
    def _normalize_employee_id(cls, value: str) -> str:
        return value.strip()

    @field_validator("part_code")
    @classmethod
    def _normalize_part_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        return normalized or None

    @field_validator("effective_from", "effective_to")
    @classmethod
    def _validate_iso_date_or_none(cls, value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        normalized = str(value).strip()
        date.fromisoformat(normalized)
        return normalized

    @model_validator(mode="after")
    def _validate_business_rules(self):
        if not isinstance(self.payload, dict) or not self.payload:
            raise ValueError("payload cannot be empty")

        if self.category == ServiceEventCategory.APPOINTMENT:
            appointment_order_no = str(self.payload.get("appointment_order_no") or "").strip()
            appointment_order_date = str(self.payload.get("appointment_order_date") or "").strip()
            if appointment_order_no and not str(self.payload.get("order_no") or "").strip():
                self.payload["order_no"] = appointment_order_no
            if appointment_order_date and not str(self.payload.get("order_date") or "").strip():
                self.payload["order_date"] = appointment_order_date

        missing = [
            key
            for key in REQUIRED_PAYLOAD_KEYS_BY_CATEGORY.get(self.category, ())
            if not str(self.payload.get(key) or "").strip()
        ]
        if missing:
            raise ValueError(
                "payload missing required keys for "
                f"{self.category.value}: {', '.join(sorted(missing))}"
            )

        required_order_metadata = tuple(dict.fromkeys(
            GLOBAL_MANDATORY_ORDER_METADATA
            + MANDATORY_ORDER_METADATA_BY_CATEGORY.get(self.category, ())
        ))
        missing_order_metadata = [
            key
            for key in required_order_metadata
            if not str(self.payload.get(key) or "").strip()
        ]
        if missing_order_metadata:
            raise ValueError(
                "payload missing mandatory order metadata for "
                f"{self.category.value}: {', '.join(sorted(missing_order_metadata))}"
            )

        if self.category == ServiceEventCategory.CPC_PAY_FIXATION:
            _validate_cpc_fixation_payload(self.payload)
        else:
            cpc_raw = self.payload.get("cpc")
            cpc_value = str(cpc_raw).strip().upper() if cpc_raw not in (None, "") else None
            if cpc_value:
                cpc_required_keys = CPC_PAYLOAD_KEYS_BY_CATEGORY.get(cpc_value, {}).get(self.category.value, ())
                missing_cpc = [
                    key
                    for key in cpc_required_keys
                    if not str(self.payload.get(key) or "").strip()
                ]
                if missing_cpc:
                    raise ValueError(
                        "payload missing CPC keys for "
                        f"{self.category.value}/{cpc_value}: {', '.join(sorted(missing_cpc))}"
                    )
            elif self.category in {
                ServiceEventCategory.PAY,
                ServiceEventCategory.INCREMENT,
            }:
                raise ValueError("payload.cpc is required for pay-related events")

        pay_change = self.payload.get("pay_change")
        if pay_change is not None:
            if not isinstance(pay_change, dict):
                raise ValueError("pay_change must be an object")
            affects_pay = pay_change.get("affects_pay")
            if not isinstance(affects_pay, bool):
                raise ValueError("pay_change.affects_pay must be boolean")
            if affects_pay:
                for key in ("old_basic", "new_basic", "effective_from"):
                    if pay_change.get(key) in (None, ""):
                        raise ValueError(
                            f"pay_change.{key} is required when pay_change.affects_pay is true"
                        )
                try:
                    if float(pay_change.get("old_basic")) <= 0 or float(pay_change.get("new_basic")) <= 0:
                        raise ValueError("pay_change old_basic and new_basic must be positive")
                except (TypeError, ValueError) as exc:
                    raise ValueError("pay_change old_basic and new_basic must be numeric") from exc
                date.fromisoformat(str(pay_change.get("effective_from")))

        if self.category == ServiceEventCategory.CPC_PAY_FIXATION and not self.effective_from:
            self.effective_from = str(self.payload.get("effective_date") or "").strip() or None

        if self.effective_from and self.effective_to:
            if date.fromisoformat(self.effective_to) < date.fromisoformat(self.effective_from):
                raise ValueError("effective_to cannot be earlier than effective_from")

        return self


def normalize_service_event_input(raw: dict[str, Any]) -> CanonicalServiceEventInput:
    category_raw = (
        raw.get("category")
        or raw.get("event_category")
        or raw.get("event_type")
        or raw.get("eventType")
        or raw.get("type")
        or raw.get("event_name")
        or raw.get("eventName")
        or ServiceEventCategory.GENERIC.value
    )
    category = ServiceEventCategory(_normalize_category_value(category_raw))

    payload = raw.get("payload") or {}
    payload_with_subtype = dict(payload)
    payload_with_subtype.pop("event_subtype", None)
    payload_with_subtype.pop("eventSubtype", None)
    if category == ServiceEventCategory.CPC_PAY_FIXATION:
        payload_with_subtype = _normalize_cpc_fixation_payload(raw, payload_with_subtype)

    inferred_part_code = EVENT_CATEGORY_TO_PART_CODE.get(category)
    requested_part_code = raw.get("part_code") or raw.get("part_key")
    effective_from = raw.get("effective_from")
    if category == ServiceEventCategory.CPC_PAY_FIXATION:
        effective_from = effective_from or payload_with_subtype.get("effective_date")

    return CanonicalServiceEventInput(
        employee_id=str(raw.get("employee_id") or "").strip(),
        category=category,
        payload=payload_with_subtype,
        effective_from=effective_from,
        effective_to=raw.get("effective_to"),
        part_code=inferred_part_code or requested_part_code,
    )
