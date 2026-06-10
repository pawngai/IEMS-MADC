from __future__ import annotations

from typing import Any

from contexts.service_book.records.schemas.service_event_types import CPC_OPTIONS, PayCommission, ServiceEventCategory
# -- CPC-specific field definitions ----------------------------------------

_PAY_BAND_OPTIONS = [
    "PB-1 (5200-20200)",
    "PB-2 (9300-34800)",
    "PB-3 (15600-39100)",
    "PB-4 (37400-67000)",
]

_PAY_SCALE_OPTIONS_4TH_CPC = [
    "750-12-870-14-940",
    "775-12-871-12-1025",
    "775-12-871-14-955-15-1030-20-1150",
    "800-15-1010-20-1150",
    "825-15-900-20-1200",
    "950-20-1150-25-1400",
    "950-20-1150-25-1500",
    "1150-25-1500",
    "975-25-1150-30-1540",
    "975-25-1150-30-1660",
    "1200-30-1440-30-1800",
    "1200-30-1560-40-2040",
    "1320-30-1560-40-2040",
    "1350-30-1440-40-1800-50-2200",
    "1400-40-1800-50-2300",
    "1400-40-1600-50-2300-60-2600",
    "1600-50-2300-60-2660",
    "1640-60-2600-75-2900",
    "2000-60-2120",
    "2000-60-2300-75-3200",
    "2000-60-2300-75-3200-100-3500",
    "2375-75-3200-100-3500",
    "2375-75-3200-100-3500-125-3750",
    "2500-4000",
    "2200-75-2800-100-4000",
    "2300-100-2800",
    "2630/- (Fixed)",
    "2630-75-2780",
    "3150-100-3350",
    "3000-125-3625",
    "3000-100-3500-125-4500",
    "3000-100-3500-125-5000",
    "3200-100-3700-125-4700",
    "3700-150-4450",
    "3700-125-4700-150-5000",
    "3950-125-4700-150-5000",
    "3700-125-4950-150-5700",
    "4100-125-4850-150-5300",
    "4500-150-5700",
    "4800-150-5700",
    "5100-150-5700",
    "5100-150-6150",
    "5100-150-5700-200-6300",
    "5100-150-6300-200-6700",
    "4500-150-5700-200-7300",
    "5900-200-6700",
    "5900-200-7300",
    "7300-100-7600",
    "7300-200-7500-250-8000",
    "7600/- (Fixed)",
    "7600-100-8000",
    "8000/- (Fixed)",
    "9000/- (Fixed)",
]

_PAY_SCALE_OPTIONS_5TH_CPC = [
    "2550-55-2660-60-3200",
    "2610-60-3150-65-3540",
    "2610-60-2910-65-3300-70-4000",
    "2650-65-3300-70-4000",
    "2750-70-3800-75-4400",
    "3050-75-3950-80-4590",
    "3200-85-4900",
    "4000-100-6000",
    "4500-125-7000",
    "5000-150-8000",
    "5500-175-9000",
    "6500-200-6900",
    "6500-200-10500",
    "7450-225-11500",
    "7500-250-12000",
    "8000-275-13500",
    "9000",
    "9000-275-9550",
    "10325-325-10975",
    "10000-325-15200",
    "10650-325-15850",
    "12000-375-16500",
    "12750-375-16500",
    "12000-375-18000",
    "14300-400-18300",
    "15100-400-18300",
    "16400-450-20000",
    "16400-450-20900",
    "14300-450-22400",
    "18400-500-22400",
    "22400-525-24500",
    "22400-600-26000",
    "24050-650-26000",
    "26000/- (Fixed)",
    "30000/- (Fixed)",
]

_GRADE_PAY_OPTIONS = [
    "1800", "1900", "2000", "2400", "2800",
    "4200", "4400", "4600", "4800", "5400",
    "6600", "7600", "8700", "8900", "10000",
]

_PAY_LEVEL_OPTIONS = [
    "Level 1",
    "Level 1A",
    "Level 2",
    "Level 3",
    "Level 4",
    "Level 5",
    "Level 6",
    "Level 7",
    "Level 8",
    "Level 9",
    "Level 10",
    "Level 10A",
    "Level 11",
    "Level 11A",
    "Level 12",
    "Level 13",
    "Level 13A",
    "Level 14",
]

CPC_FIELD_DEFINITIONS: dict[str, dict[str, Any]] = {
    # 4th / 5th CPC (scale-based)
    "pay_scale": {
        "label": "Pay Scale",
        "type": "select",
        "optionsByCpc": {
            PayCommission.CPC_4.value: _PAY_SCALE_OPTIONS_4TH_CPC,
            PayCommission.CPC_5.value: _PAY_SCALE_OPTIONS_5TH_CPC,
        },
    },
    "from_pay_scale": {
        "label": "From Pay Scale",
        "type": "select",
        "optionsByCpc": {
            PayCommission.CPC_4.value: _PAY_SCALE_OPTIONS_4TH_CPC,
            PayCommission.CPC_5.value: _PAY_SCALE_OPTIONS_5TH_CPC,
        },
    },
    "to_pay_scale": {
        "label": "To Pay Scale",
        "type": "select",
        "optionsByCpc": {
            PayCommission.CPC_4.value: _PAY_SCALE_OPTIONS_4TH_CPC,
            PayCommission.CPC_5.value: _PAY_SCALE_OPTIONS_5TH_CPC,
        },
    },
    # 6th CPC (pay band + grade pay)
    "pay_band": {
        "label": "Pay Band",
        "type": "select",
        "options": _PAY_BAND_OPTIONS,
    },
    "grade_pay": {
        "label": "Grade Pay",
        "type": "select",
        "options": _GRADE_PAY_OPTIONS,
    },
    "from_pay_band": {
        "label": "From Pay Band",
        "type": "select",
        "options": _PAY_BAND_OPTIONS,
    },
    "from_grade_pay": {
        "label": "From Grade Pay",
        "type": "select",
        "options": _GRADE_PAY_OPTIONS,
    },
    "to_pay_band": {
        "label": "To Pay Band",
        "type": "select",
        "options": _PAY_BAND_OPTIONS,
    },
    "to_grade_pay": {
        "label": "To Grade Pay",
        "type": "select",
        "options": _GRADE_PAY_OPTIONS,
    },
    # 7th CPC (pay level + matrix)
    "pay_level": {
        "label": "Pay Level",
        "type": "select",
        "options": _PAY_LEVEL_OPTIONS,
    },
    "from_pay_level": {
        "label": "From Pay Level",
        "type": "select",
        "options": _PAY_LEVEL_OPTIONS,
    },
    "to_pay_level": {
        "label": "To Pay Level",
        "type": "select",
        "options": _PAY_LEVEL_OPTIONS,
    },
    "pay_cell_index": {"label": "Cell Index", "type": "number"},
    "from_pay_cell_index": {"label": "From Cell Index", "type": "number"},
    # Common across CPCs
    "basic_pay": {"label": "Basic Pay", "type": "number"},
    "from_basic_pay": {"label": "From Basic Pay", "type": "number"},
    "to_basic_pay": {"label": "To Basic Pay", "type": "number"},
}


# CPC-specific payload keys by CPC → Category.
# Categories that do not involve pay structure get empty tuples.
CPC_PAYLOAD_KEYS_BY_CATEGORY: dict[str, dict[str, tuple[str, ...]]] = {
    PayCommission.CPC_4.value: {
        "APPOINTMENT": ("pay_scale", "basic_pay"),
        "CONFIRMATION": (),
        "PROMOTION": ("from_pay_scale", "to_pay_scale", "from_basic_pay", "to_basic_pay"),
        "TRANSFER": (),
        "PAY": ("pay_scale", "from_basic_pay", "to_basic_pay"),
        "INCREMENT": ("pay_scale", "from_basic_pay", "to_basic_pay"),
        "DEPUTATION": ("pay_scale", "basic_pay"),
        "SUSPENSION": (),
        "REINSTATEMENT": ("pay_scale", "basic_pay"),
        "RETIREMENT": ("pay_scale", "basic_pay"),
        "DISCIPLINARY": (),
        "CUSTOM": (),
        "GENERIC": (),
        "FINANCIAL_UPGRADATION": ("from_pay_scale", "to_pay_scale", "from_basic_pay", "to_basic_pay"),
        "CPC_PAY_FIXATION": ("pay_scale", "from_basic_pay", "to_basic_pay"),
    },
    PayCommission.CPC_5.value: {
        "APPOINTMENT": ("pay_scale", "basic_pay"),
        "CONFIRMATION": (),
        "PROMOTION": ("from_pay_scale", "to_pay_scale", "from_basic_pay", "to_basic_pay"),
        "TRANSFER": (),
        "PAY": ("pay_scale", "from_basic_pay", "to_basic_pay"),
        "INCREMENT": ("pay_scale", "from_basic_pay", "to_basic_pay"),
        "DEPUTATION": ("pay_scale", "basic_pay"),
        "SUSPENSION": (),
        "REINSTATEMENT": ("pay_scale", "basic_pay"),
        "RETIREMENT": ("pay_scale", "basic_pay"),
        "DISCIPLINARY": (),
        "CUSTOM": (),
        "GENERIC": (),
        "FINANCIAL_UPGRADATION": ("from_pay_scale", "to_pay_scale", "from_basic_pay", "to_basic_pay"),
        "CPC_PAY_FIXATION": ("pay_scale", "from_basic_pay", "to_basic_pay"),
    },
    PayCommission.CPC_6.value: {
        "APPOINTMENT": ("pay_band", "grade_pay", "basic_pay"),
        "CONFIRMATION": (),
        "PROMOTION": ("from_pay_band", "from_grade_pay", "to_pay_band", "to_grade_pay", "from_basic_pay", "to_basic_pay"),
        "TRANSFER": (),
        "PAY": ("pay_band", "grade_pay", "from_basic_pay", "to_basic_pay"),
        "INCREMENT": ("pay_band", "grade_pay", "from_basic_pay", "to_basic_pay"),
        "DEPUTATION": ("pay_band", "grade_pay", "basic_pay"),
        "SUSPENSION": (),
        "REINSTATEMENT": ("pay_band", "grade_pay", "basic_pay"),
        "RETIREMENT": ("pay_band", "grade_pay", "basic_pay"),
        "DISCIPLINARY": (),
        "CUSTOM": (),
        "GENERIC": (),
        "FINANCIAL_UPGRADATION": ("from_pay_band", "from_grade_pay", "to_pay_band", "to_grade_pay", "from_basic_pay", "to_basic_pay"),
        "CPC_PAY_FIXATION": ("pay_band", "grade_pay", "from_basic_pay", "to_basic_pay"),
    },
    PayCommission.CPC_7.value: {
        "APPOINTMENT": ("pay_level", "basic_pay"),
        "CONFIRMATION": (),
        "PROMOTION": ("from_pay_level", "to_pay_level", "from_basic_pay", "to_basic_pay"),
        "TRANSFER": (),
        "PAY": ("pay_level", "pay_cell_index", "from_basic_pay", "to_basic_pay"),
        "INCREMENT": ("pay_level", "pay_cell_index", "from_basic_pay", "to_basic_pay"),
        "DEPUTATION": ("pay_level", "basic_pay"),
        "SUSPENSION": (),
        "REINSTATEMENT": ("pay_level", "basic_pay"),
        "RETIREMENT": ("pay_level", "basic_pay"),
        "DISCIPLINARY": (),
        "CUSTOM": (),
        "GENERIC": (),
        "FINANCIAL_UPGRADATION": ("from_pay_level", "to_pay_level", "from_basic_pay", "to_basic_pay"),
        "CPC_PAY_FIXATION": ("pay_level", "pay_cell_index", "from_basic_pay", "to_basic_pay"),
    },
}


# All service events record to Part IV: History of Service.
EVENT_CATEGORY_TO_PART_CODE: dict[ServiceEventCategory, str] = {
    category: "IV" for category in ServiceEventCategory
}


REQUIRED_PAYLOAD_KEYS_BY_CATEGORY: dict[ServiceEventCategory, tuple[str, ...]] = {
    ServiceEventCategory.APPOINTMENT: (
        "appointment_order_no",
        "appointment_order_date",
        "post_name",
        "office_name",
        "service_group",
    ),
    ServiceEventCategory.CONFIRMATION: ("confirmation_date",),
    ServiceEventCategory.PROMOTION: ("promotion_date", "to_post", "promotion_type"),
    ServiceEventCategory.TRANSFER: ("transfer_date", "transfer_type", "to_office"),
    ServiceEventCategory.PAY: ("grant_date", "to_level"),
    ServiceEventCategory.INCREMENT: (
        "increment_date",
        "increment_type",
    ),
    ServiceEventCategory.DEPUTATION: ("from_date", "borrowing_department"),
    ServiceEventCategory.SUSPENSION: ("suspension_date", "reason"),
    ServiceEventCategory.REINSTATEMENT: ("reinstatement_date", "reinstatement_type"),
    ServiceEventCategory.RETIREMENT: ("retirement_type", "retirement_date"),
    ServiceEventCategory.DISCIPLINARY: ("penalty_type", "penalty_date"),
    ServiceEventCategory.CUSTOM: (),
    ServiceEventCategory.GENERIC: (),
    ServiceEventCategory.FINANCIAL_UPGRADATION: (
        "upgradation_date",
        "upgradation_type",
    ),
    ServiceEventCategory.CPC_PAY_FIXATION: (
        "effective_date",
    ),
}


CANONICAL_CATEGORY_OPTIONS: tuple[dict[str, str], ...] = tuple(
    {
        "value": category.value,
        "label": category.value.replace("_", " ").title(),
    }
    for category in ServiceEventCategory
    if category not in {ServiceEventCategory.PAY, ServiceEventCategory.CONFIRMATION, ServiceEventCategory.GENERIC}
)


FIELD_DEFINITIONS: dict[str, dict[str, Any]] = {
    "appointment_order_no": {"label": "Appointment Order No", "type": "text"},
    "appointment_order_date": {"label": "Appointment Order Date", "type": "date"},
    "effective_date": {"label": "Effective Date", "type": "date"},
    "post_name": {"label": "Post Name", "type": "text"},
    "office_name": {"label": "Office Name", "type": "text"},
    "service": {"label": "Service", "type": "text"},
    "service_group": {"label": "Service Group", "type": "text"},
    "grade": {"label": "Grade", "type": "text"},
    "joining_date": {"label": "Joining Date", "type": "date"},
    "joining_office": {"label": "Joining Office", "type": "text"},
    "probation_start_date": {"label": "Probation Start", "type": "date"},
    "probation_end_date": {"label": "Probation End", "type": "date"},
    "extension_from": {"label": "Extension From", "type": "date"},
    "extension_to": {"label": "Extension To", "type": "date"},
    "extension_reason": {"label": "Extension Reason", "type": "text"},
    "confirmation_date": {"label": "Effective Date", "type": "date"},
    "regularization_date": {"label": "Regularization Date", "type": "date"},
    "previous_status": {"label": "Previous Status", "type": "text"},
    "reemployment_date": {"label": "Re-employment Date", "type": "date"},
    "tenure_end_date": {"label": "Tenure End Date", "type": "date"},
    "posting_date": {"label": "Posting Date", "type": "date"},
    "transfer_date": {"label": "Effective Date", "type": "date"},
    "transfer_type": {
        "label": "Transfer Type",
        "type": "select",
        "options": ["office", "station", "administrative", "mutual", "inter_departmental"],
    },
    "to_office": {"label": "To Office", "type": "text"},
    "to_service": {"label": "To Service", "type": "text"},
    "to_service_group": {"label": "To Service Group", "type": "text"},
    "to_grade": {"label": "To Grade", "type": "text"},
    "promotion_date": {"label": "Effective Date", "type": "date"},
    "to_post": {"label": "To Post", "type": "text"},
    "promotion_type": {
        "label": "Promotion Type",
        "type": "select",
        "options": ["officiating", "ad_hoc", "regular"],
    },
    "grant_date": {"label": "Effective Date", "type": "date"},
    "scheme_type": {"label": "Scheme Type", "type": "text"},
    "to_level": {"label": "To Level", "type": "text"},
    "pay_matrix_cell": {"label": "Pay Matrix Cell", "type": "number"},
    "arrears_amount": {"label": "Arrears Amount", "type": "number"},
    "increment_date": {"label": "Effective Date", "type": "date"},
    "increment_type": {
        "label": "Increment Type",
        "type": "select",
        "options": ["annual", "stagnation", "notional", "withheld_restored"],
    },
    "increment_amount": {"label": "Increment Amount", "type": "number"},
    "next_increment_date": {"label": "Next Increment Date", "type": "date"},
    "option_exercise_date": {"label": "Option Exercise Date", "type": "date"},
    "from_date": {"label": "Effective Date", "type": "date"},
    "borrowing_department": {"label": "Borrowing Department", "type": "text"},
    "return_date": {"label": "Return Date", "type": "date"},
    "organization": {"label": "Organization", "type": "text"},
    "training_name": {"label": "Training Name", "type": "text"},
    "completion_date": {"label": "Completion Date", "type": "date"},
    "suspension_date": {"label": "Effective Date", "type": "date"},
    "reason": {"label": "Reason", "type": "text"},
    "revocation_date": {"label": "Revocation Date", "type": "date"},
    "penalty_type": {"label": "Penalty Type", "type": "text"},
    "penalty_date": {"label": "Effective Date", "type": "date"},
    "reinstatement_date": {"label": "Effective Date", "type": "date"},
    "reinstatement_type": {"label": "Reinstatement Type", "type": "text"},
    "break_from": {"label": "Break From", "type": "date"},
    "break_to": {"label": "Break To", "type": "date"},
    "condonation_order_date": {"label": "Condonation Order Date", "type": "date"},
    "break_reference": {"label": "Break Reference", "type": "text"},
    "retirement_type": {"label": "Retirement Type", "type": "text"},
    "retirement_date": {"label": "Effective Date", "type": "date"},
    "resignation_date": {"label": "Resignation Date", "type": "date"},
    "acceptance_date": {"label": "Acceptance Date", "type": "date"},
    "termination_date": {"label": "Termination Date", "type": "date"},
    "grounds": {"label": "Grounds", "type": "text"},
    "dismissal_date": {"label": "Dismissal Date", "type": "date"},
    "disciplinary_case_no": {"label": "Disciplinary Case No", "type": "text"},
    "date_of_death": {"label": "Date of Death", "type": "date"},
    "upgradation_date": {"label": "Effective Date", "type": "date"},
    "effective_date": {"label": "Effective Date", "type": "date"},
    "upgradation_type": {
        "label": "Upgradation Type",
        "type": "select",
        "options": ["1st", "2nd", "3rd"],
    },
    "fixation_date": {"label": "Effective Date", "type": "date"},
}


def get_service_event_form_schema() -> dict[str, Any]:
    return {
        "canonical_category_options": list(CANONICAL_CATEGORY_OPTIONS),
        "category_to_part_code": {
            category.value: part_code
            for category, part_code in EVENT_CATEGORY_TO_PART_CODE.items()
        },
        "required_payload_keys_by_category": {
            category.value: list(keys)
            for category, keys in REQUIRED_PAYLOAD_KEYS_BY_CATEGORY.items()
        },
        "field_definitions": FIELD_DEFINITIONS,
        "pay_change": {
            "enabled": True,
            "required_when_affects_pay": ["old_basic", "new_basic", "effective_from"],
        },
        "cpc_options": list(CPC_OPTIONS),
        "cpc_field_definitions": CPC_FIELD_DEFINITIONS,
        "cpc_payload_keys_by_category": {
            cpc: {cat: list(keys) for cat, keys in cat_map.items()}
            for cpc, cat_map in CPC_PAYLOAD_KEYS_BY_CATEGORY.items()
        },
    }

