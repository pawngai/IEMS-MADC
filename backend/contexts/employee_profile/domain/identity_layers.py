from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


IDENTITY_FIELDS = {
    "id",
    "employee_id",
    "employee_code",
    "full_name",
    "gender",
    "date_of_birth",
    "current_designation_id",
    "current_office_id",
    "reporting_officer_id",
    "employee_status",
    "status_effective_date",
    "status_remarks",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "version",
}

EXTENSION_FIELDS = {
    "id",
    "employee_id",
    "employment_type",
    "date_of_initial_engagement",
    "current_department_id",
    "contract_order_no",
    "contract_start_date",
    "contract_end_date",
    "consolidated_pay",
    "contract_authority",
    "vendor_agency",
    "renewal_allowed",
    "engagement_order_no",
    "engagement_order_date",
    "engagement_end_date",
    "remuneration_type",
    "muster_roll_number",
    "daily_wage_rate",
    "wage_rate_unit",
    "engagement_office",
    "nature_of_work",
    "expected_duration_days",
    "fixed_monthly_amount",
    "basic_pay",
    "pay_level",
    "document_ids",
    "engagement_remarks",
    "deputation_order_no",
    "parent_department",
    "parent_designation",
    "lien_status",
    "deputation_start_date",
    "deputation_end_date",
    "deputation_allowance_percent",
    "outsourcing_order_no",
    "agency_name",
    "agency_contract_number",
    "sla_reference",
    "monthly_billing_rate",
    "role_description",
    "father_name",
    "mother_name",
    "nationality",
    "category",
    "sub_caste",
    "religion",
    "date_of_birth_saka",
    "place_of_birth",
    "blood_group",
    "height_cm",
    "identification_marks",
    "marital_status",
    "spouse_name",
    "educational_qualifications_initial",
    "educational_qualifications_acquired",
    "professional_qualifications",
    "contact",
    "identifiers",
    "photo_url",
    "photo_updated_at",
    "signature_url",
    "thumb_impression_url",
    "workflow_status",
    "workflow_remarks",
    "employee_section_completed",
    "data_entry_section_completed",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "verified_at",
    "verified_by",
    "approved_at",
    "approved_by",
    "locked_at",
    "locked_by",
    "version",
}

CONTACT_FIELDS = {
    "mobile_primary",
    "mobile_alternate",
    "email_personal",
    "email_official",
    "address_line1",
    "address_line2",
    "city",
    "district",
    "state",
    "pincode",
    "present_address_line1",
    "present_address_line2",
    "present_city",
    "present_district",
    "present_state",
    "present_pincode",
    "emergency_name",
    "emergency_phone",
    "emergency_relation",
}

IDENTIFIER_FIELDS = {
    "aadhaar_number",
    "pan_number",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_document(doc: dict[str, Any] | None) -> dict[str, Any]:
    return deepcopy(doc or {})


def _has_profile_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def split_employee_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    data = normalize_document(payload)
    identity: dict[str, Any] = {}
    extension: dict[str, Any] = {}

    for key, value in data.items():
        if key in IDENTITY_FIELDS:
            identity[key] = value
            continue
        if key in EXTENSION_FIELDS:
            extension[key] = value
            continue
        if key in CONTACT_FIELDS:
            extension.setdefault("contact", {})[key] = value
            continue
        if key in IDENTIFIER_FIELDS:
            extension.setdefault("identifiers", {})[key] = value

    employee_id = identity.get("employee_id") or extension.get("employee_id")
    if employee_id:
        identity.setdefault("employee_id", employee_id)
        extension.setdefault("employee_id", employee_id)

    return identity, extension


def compose_employee_record_view(
    identity: dict[str, Any] | None,
    extension: dict[str, Any] | None,
) -> dict[str, Any]:
    identity_doc = normalize_document(identity)
    extension_doc = normalize_document(extension)
    if not identity_doc and not extension_doc:
        return {}

    identity_workflow_status = str(identity_doc.get("workflow_status") or "").strip().upper()
    identity_doc.pop("workflow_status", None)
    composed = {**identity_doc, **extension_doc}
    if identity_workflow_status:
        composed["identity_workflow_status"] = identity_workflow_status
    contact = normalize_document(extension_doc.get("contact"))
    identifiers = normalize_document(extension_doc.get("identifiers"))
    composed["contact"] = contact
    composed["identifiers"] = identifiers

    for field in CONTACT_FIELDS:
        if field in contact and _has_profile_value(contact[field]):
            composed[field] = contact[field]
    for field in IDENTIFIER_FIELDS:
        if field in identifiers and field not in composed:
            composed[field] = identifiers[field]

    if "created_at" not in composed:
        composed["created_at"] = identity_doc.get("created_at") or extension_doc.get("created_at")
    if "updated_at" not in composed:
        composed["updated_at"] = extension_doc.get("updated_at") or identity_doc.get("updated_at")
    if "version" not in composed:
        composed["version"] = max(int(identity_doc.get("version") or 1), int(extension_doc.get("version") or 1))
    workflow_status = str(composed.get("workflow_status") or "").strip().upper()
    composed["workflow_status"] = workflow_status or "DRAFT"

    return composed


def extract_identity_patch(update_fields: dict[str, Any]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for key, value in normalize_document(update_fields).items():
        if key in IDENTITY_FIELDS and key not in {"id", "employee_id", "created_at", "created_by"}:
            patch[key] = value
    return patch


def extract_extension_patch(update_fields: dict[str, Any]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for key, value in normalize_document(update_fields).items():
        if key in EXTENSION_FIELDS and key not in {"id", "employee_id", "created_at", "created_by"}:
            patch[key] = value
        elif key.startswith("contact.") or key.startswith("identifiers."):
            patch[key] = value
        elif key in CONTACT_FIELDS:
            patch[f"contact.{key}"] = value
        elif key in IDENTIFIER_FIELDS:
            patch[f"identifiers.{key}"] = value
    return patch
