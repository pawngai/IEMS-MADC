from __future__ import annotations

from typing import Any

from contexts.service_book.contracts.servicebook.schema_definition import SCHEMA_DEFINITIONS


SERVICEBOOK_UI_SCHEMA_BY_KEY: dict[str, dict[str, Any]] = {
    "SB_I_BIODATA": {
        "form_id": "service_book_part_i",
        "title": "Service Book - Part I (Bio-Data)",
        "sections": [],
    },
    "SB_IIA_IMMUTABLE_CERTS": {
        "form_id": "service_book_part_ii_a",
        "title": "Service Book - Part II-A",
        "sections": [],
    },
    "SB_IIB_FAMILY_SHEET": {
        "form_id": "service_book_part_ii_b",
        "title": "Service Book - Part II-B",
        "sections": [],
    },
    "SB_III_TOTAL_QS_SUMMARY": {
        "form_id": "service_book_part_iii",
        "title": "Service Book - Part III",
        "sections": [],
    },
    "SB_IV_SERVICE_HISTORY_ROW": {
        "form_id": "service_book_part_iv",
        "title": "Service Book - Part IV",
        "sections": [],
    },
    "SB_V_SERVICE_VERIFICATION_ROW": {
        "form_id": "service_book_part_v",
        "title": "Service Book - Part V",
        "sections": [],
    },
    "SB_VI_LEAVE_OPENING_BALANCE": {
        "form_id": "service_book_part_vi",
        "title": "Service Book - Part VI",
        "sections": [],
    },
    "SB_VII_LTC_ROW": {
        "form_id": "service_book_part_vii",
        "title": "Service Book - Part VII",
        "sections": [],
    },
    "SB_VIII_AUDIT_COMMENT": {
        "form_id": "service_book_part_viii",
        "title": "Service Book - Part VIII",
        "sections": [],
    },
}


SERVICEBOOK_FIELDS_BY_SCHEMA_KEY: dict[str, list[dict[str, Any]]] = {
    "SB_I_BIODATA": [
        {"key": "name_in_block_letters", "type": "string", "required": True},
        {"key": "father_name", "type": "string", "required": True},
        {"key": "marital_status", "type": "string", "required": True},
        {"key": "caste_category", "type": "string", "required": True},
        {"key": "date_of_birth_christian", "type": "date", "required": True},
        {
            "key": "educational_qualifications_initial",
            "type": "array",
            "required": False,
        },
    ],
    "SB_IIA_IMMUTABLE_CERTS": [
        {"key": "medical_fitness_certificate", "type": "boolean", "required": False},
        {"key": "character_verification_done", "type": "boolean", "required": False},
        {"key": "entries_confirmed", "type": "boolean", "required": False},
    ],
    "SB_IIB_FAMILY_SHEET": [
        {"key": "family_members", "type": "array", "required": False},
        {"key": "family_declaration_date", "type": "date", "required": False},
    ],
    "SB_IIB_PCF_NOMINATION_ROW": [
        {"key": "pcf_account_number", "type": "string", "required": False},
        {"key": "pcf_nomination", "type": "array", "required": False},
        {"key": "pcf_nomination_date", "type": "date", "required": False},
    ],
    "SB_IIB_DCRG_NOMINATION_ROW": [
        {"key": "dcr_gratuity_nomination", "type": "array", "required": False},
        {"key": "dcr_gratuity_nomination_date", "type": "date", "required": False},
    ],
    "SB_IIB_NPS_NOMINATION_ROW": [
        {"key": "nps_nomination", "type": "array", "required": False},
        {"key": "nps_nomination_date", "type": "date", "required": False},
    ],
    "SB_IIB_LEAVE_ENCASHMENT_NOMINATION_ROW": [
        {"key": "leave_encashment_nomination", "type": "array", "required": False},
        {"key": "leave_encashment_nomination_date", "type": "date", "required": False},
    ],
    "SB_IIB_FAMILY_PENSION_NOMINATION_ROW": [
        {"key": "family_pension_nomination", "type": "array", "required": False},
        {"key": "family_pension_nomination_date", "type": "date", "required": False},
    ],
    "SB_IIB_BANK_DETAILS": [
        {"key": "bank_account_number", "type": "string", "required": False},
        {"key": "bank_name", "type": "string", "required": False},
        {"key": "bank_ifsc", "type": "string", "required": False},
    ],
    "SB_IIB_NPS_PRAN": [
        {"key": "nps_pran_number", "type": "string", "required": False},
    ],
    "SB_III_PREVIOUS_SERVICE_ROW": [
        {"key": "service_from", "type": "date", "required": True},
        {"key": "service_to", "type": "date", "required": True},
        {"key": "post_held", "type": "string", "required": True},
        {"key": "organization", "type": "string", "required": True},
    ],
    "SB_III_FOREIGN_SERVICE_ROW": [
        {"key": "service_from", "type": "date", "required": True},
        {"key": "service_to", "type": "date", "required": True},
        {"key": "post_held", "type": "string", "required": True},
        {"key": "employer", "type": "string", "required": True},
    ],
    "SB_III_TOTAL_QS_SUMMARY": [
        {
            "key": "total_previous_qualifying_service",
            "type": "object",
            "required": False,
        },
        {"key": "verified", "type": "boolean", "required": False},
        {"key": "verified_by", "type": "string", "required": False},
        {"key": "verification_date", "type": "date", "required": False},
    ],
    "SB_IV_SERVICE_HISTORY_ROW": [
        {"key": "period_from", "type": "date", "required": True},
        {"key": "period_to", "type": "date", "required": False},
        {"key": "office_station", "type": "string", "required": True},
        {"key": "post_held", "type": "string", "required": True},
        {"key": "event_type", "type": "string", "required": True},
    ],
    "SB_V_SERVICE_VERIFICATION_ROW": [
        {"key": "period_from", "type": "date", "required": True},
        {"key": "period_to", "type": "date", "required": True},
        {"key": "post_held", "type": "string", "required": True},
    ],
    "SB_VI_LEAVE_TRANSACTION_ROW": [
        {"key": "transaction_date", "type": "date", "required": True},
        {"key": "transaction_type", "type": "string", "required": True},
        {"key": "leave_type", "type": "string", "required": True},
        {"key": "opening_balance", "type": "number", "required": True},
        {"key": "closing_balance", "type": "number", "required": True},
    ],
    "SB_VI_LEAVE_OPENING_BALANCE": [
        {"key": "earned_leave_balance", "type": "number", "required": False},
        {"key": "half_pay_leave_balance", "type": "number", "required": False},
        {"key": "commuted_leave_balance", "type": "number", "required": False},
        {"key": "leave_not_due_balance", "type": "number", "required": False},
    ],
    "SB_VII_LTC_ROW": [
        {"key": "block_year", "type": "string", "required": True},
        {"key": "ltc_type", "type": "string", "required": True},
        {"key": "availed_date", "type": "date", "required": True},
    ],
    "SB_VII_HBA_ROW": [
        {"key": "sanction_date", "type": "date", "required": True},
        {"key": "sanction_order_number", "type": "string", "required": True},
        {"key": "amount_sanctioned", "type": "number", "required": True},
    ],
    "SB_VII_VEHICLE_ADVANCE_ROW": [
        {"key": "vehicle_advance_records", "type": "array", "required": False},
    ],
    "SB_VII_FESTIVAL_ADVANCE_ROW": [
        {"key": "festival_advance_records", "type": "array", "required": False},
    ],
    "SB_VIII_AUDIT_COMMENT": [
        {"key": "comment_date", "type": "date", "required": True},
        {"key": "audit_type", "type": "string", "required": True},
        {"key": "auditor_name", "type": "string", "required": True},
        {"key": "comment_text", "type": "string", "required": True},
        {"key": "severity", "type": "string", "required": True},
    ],
}