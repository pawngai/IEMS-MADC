# Employment-Type-Driven Dynamic Employee Form Schema
# Compliant - Employee Profile ≠ Service Book

from typing import List, Dict, Optional

from app_platform.reference_data.infrastructure.employee_form_types import (
    EMPLOYMENT_TYPE_CODE_MAP,
    EmploymentType,
)
from app_platform.reference_data.infrastructure import employee_form_validation

# ==================== COMMON FIELDS (ALWAYS VISIBLE) ====================

COMMON_FIELDS = [
    {
        "field_id": "employee_id",
        "label": "Employee ID",
        "type": "text",
        "required": False,
        "readonly": True,
        "auto_generated": True,
        "placeholder": "Auto-generated",
        "step": 1,
        "section": "identification"
    },
    {
        "field_id": "full_name",
        "label": "Full Name",
        "type": "text",
        "required": True,
        "validation": {"pattern": r"^[A-Za-z\s]+$", "min_length": 2, "max_length": 100},
        "placeholder": "Enter full name as per official records",
        "step": 1,
        "section": "personal"
    },
    {
        "field_id": "gender",
        "label": "Gender",
        "type": "select",
        "required": True,
        "options": [
            {"value": "Male", "label": "Male"},
            {"value": "Female", "label": "Female"},
            {"value": "Transgender", "label": "Transgender"}
        ],
        "step": 1,
        "section": "personal"
    },
    {
        "field_id": "date_of_birth",
        "label": "Date of Birth",
        "type": "date",
        "required": True,
        "validation": {"min_age": 18, "max_age": 65},
        "step": 1,
        "section": "personal"
    },
    {
        "field_id": "nationality",
        "label": "Nationality",
        "type": "select",
        "required": True,
        "options": [
            {"value": "Indian", "label": "Indian"},
            {"value": "Other", "label": "Other"}
        ],
        "default": "Indian",
        "step": 1,
        "section": "personal"
    },
    {
        "field_id": "category",
        "label": "Category (Reservation)",
        "type": "select",
        "required": True,
        "master_ref": "caste_categories",
        "options": [
            {"value": "GEN", "label": "General"},
            {"value": "SC", "label": "Scheduled Caste"},
            {"value": "ST", "label": "Scheduled Tribe"},
            {"value": "OBC", "label": "Other Backward Class"},
            {"value": "EWS", "label": "Economically Weaker Section"}
        ],
        "step": 1,
        "section": "personal"
    },
    {
        "field_id": "mobile_no",
        "label": "Mobile Number",
        "type": "tel",
        "required": True,
        "validation": {"pattern": r"^[6-9]\d{9}$"},
        "placeholder": "10-digit mobile number",
        "step": 2,
        "section": "contact"
    },
    {
        "field_id": "email",
        "label": "Email Address",
        "type": "email",
        "required": True,
        "validation": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
        "placeholder": "official.email@gov.in",
        "step": 2,
        "section": "contact"
    },
    {
        "field_id": "permanent_address",
        "label": "Permanent Address",
        "type": "textarea",
        "required": True,
        "validation": {"min_length": 10, "max_length": 500},
        "placeholder": "Complete permanent address",
        "step": 2,
        "section": "address"
    },
    {
        "field_id": "correspondence_address",
        "label": "Correspondence Address",
        "type": "textarea",
        "required": False,
        "validation": {"max_length": 500},
        "placeholder": "Leave blank if same as permanent address",
        "step": 2,
        "section": "address"
    },
    {
        "field_id": "department_id",
        "label": "Department",
        "type": "select",
        "required": True,
        "master_ref": "departments",
        "placeholder": "Select department",
        "step": 3,
        "section": "posting"
    },
    {
        "field_id": "office_id",
        "label": "Office",
        "type": "select",
        "required": True,
        "depends_on": "department_id",
        "placeholder": "Select office",
        "step": 3,
        "section": "posting"
    },
    {
        "field_id": "designation_id",
        "label": "Designation",
        "type": "select",
        "required": True,
        "master_ref": "designations",
        "placeholder": "Select designation",
        "step": 3,
        "section": "posting"
    },
    {
        "field_id": "employment_type",
        "label": "Employment Type",
        "type": "select",
        "required": True,
        "is_primary_switch": True,
        "options": [
            {"value": "REGULAR", "label": "Regular"},
            {"value": "CONTRACTUAL", "label": "Contractual"},
            {"value": "DAILY_WAGE", "label": "Daily Wage"},
            {"value": "DEPUTATION", "label": "Deputation"},
            {"value": "REEMPLOYED", "label": "Re-employed"},
            {"value": "OUTSOURCED", "label": "Outsourced"}
        ],
        "step": 3,
        "section": "employment"
    }
]

# ==================== EMPLOYMENT-TYPE SPECIFIC FIELDS ====================

EMPLOYMENT_TYPE_FIELDS = {
    EmploymentType.REGULAR: [
        {
            "field_id": "appointment_order_no",
            "label": "Appointment Order Number",
            "type": "text",
            "required": True,
            "validation": {"pattern": r"^[A-Za-z0-9/-]+$"},
            "placeholder": "e.g., GOV/EST/2024/001",
            "step": 4,
            "section": "appointment"
        },
        {
            "field_id": "appointment_order_date",
            "label": "Appointment Order Date",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "appointment"
        },
        {
            "field_id": "recruitment_mode",
            "label": "Mode of Recruitment",
            "type": "select",
            "required": True,
            "options": [
                {"value": "DIRECT", "label": "Direct Recruitment"},
                {"value": "PROMOTION", "label": "Promotion"},
                {"value": "DEPUTATION", "label": "Deputation"},
                {"value": "TRANSFER", "label": "Transfer"},
                {"value": "COMPASSIONATE", "label": "Compassionate Appointment"}
            ],
            "step": 4,
            "section": "appointment"
        },
        {
            "field_id": "cadre",
            "label": "Cadre",
            "type": "select",
            "required": True,
            "options": [
                {"value": "CENTRAL", "label": "Central Service"},
                {"value": "STATE", "label": "State Service"},
                {"value": "ALL_INDIA", "label": "All India Service"}
            ],
            "step": 4,
            "section": "service"
        },
        {
            "field_id": "service_group",
            "label": "Service Group",
            "type": "select",
            "required": True,
            "master_ref": "service_groups",
            "options": [
                {"value": "GRP-A", "label": "Group A"},
                {"value": "GRP-B-G", "label": "Group B (Gazetted)"},
                {"value": "GRP-B-NG", "label": "Group B (Non-Gazetted)"},
                {"value": "GRP-C", "label": "Group C"},
                {"value": "GRP-D", "label": "Group D"}
            ],
            "step": 4,
            "section": "service"
        },
        {
            "field_id": "pension_scheme",
            "label": "Pension Scheme",
            "type": "select",
            "required": True,
            "options": [
                {"value": "NPS", "label": "National Pension System (NPS)"},
                {"value": "OPS", "label": "Old Pension Scheme (OPS)"},
                {"value": "UPS", "label": "Unified Pension Scheme (UPS)"}
            ],
            "step": 4,
            "section": "service"
        },
        {
            "field_id": "retirement_date",
            "label": "Date of Superannuation",
            "type": "date",
            "required": True,
            "computed_from": "date_of_birth",
            "computation_rule": "add_years(60)",
            "step": 4,
            "section": "service"
        },
        {
            "field_id": "probation_period_months",
            "label": "Probation Period (Months)",
            "type": "number",
            "required": False,
            "default": 24,
            "validation": {"min": 0, "max": 60},
            "step": 4,
            "section": "service"
        }
    ],
    
    EmploymentType.CONTRACTUAL: [
        {
            "field_id": "contract_order_no",
            "label": "Contract Order Number",
            "type": "text",
            "required": True,
            "validation": {"pattern": r"^[A-Za-z0-9/-]+$"},
            "placeholder": "e.g., CON/2024/001",
            "step": 4,
            "section": "contract"
        },
        {
            "field_id": "contract_start_date",
            "label": "Contract Start Date",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "contract"
        },
        {
            "field_id": "contract_end_date",
            "label": "Contract End Date",
            "type": "date",
            "required": True,
            "validation": {"must_be_after": "contract_start_date"},
            "step": 4,
            "section": "contract"
        },
        {
            "field_id": "consolidated_pay",
            "label": "Consolidated Pay (₹/Month)",
            "type": "number",
            "required": True,
            "validation": {"min": 10000, "max": 500000},
            "placeholder": "Monthly consolidated amount",
            "step": 4,
            "section": "contract"
        },
        {
            "field_id": "renewal_allowed",
            "label": "Renewal Allowed",
            "type": "select",
            "required": True,
            "options": [
                {"value": "YES", "label": "Yes"},
                {"value": "NO", "label": "No"},
                {"value": "CONDITIONAL", "label": "Subject to Performance"}
            ],
            "step": 4,
            "section": "contract"
        },
        {
            "field_id": "max_renewal_count",
            "label": "Maximum Renewals",
            "type": "number",
            "required": False,
            "validation": {"min": 0, "max": 10},
            "depends_on": {"field": "renewal_allowed", "values": ["YES", "CONDITIONAL"]},
            "step": 4,
            "section": "contract"
        }
    ],
    
    EmploymentType.DAILY_WAGE: [
        {
            "field_id": "engagement_order_no",
            "label": "Engagement Order Number",
            "type": "text",
            "required": True,
            "placeholder": "e.g., DW/2024/001",
            "step": 4,
            "section": "engagement"
        },
        {
            "field_id": "engagement_date",
            "label": "Date of Appointment",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "engagement"
        },
        {
            "field_id": "wage_rate_per_day",
            "label": "Daily Wage Rate (₹)",
            "type": "number",
            "required": True,
            "validation": {"min": 100, "max": 10000},
            "placeholder": "Amount per day",
            "step": 4,
            "section": "engagement"
        },
        {
            "field_id": "nature_of_work",
            "label": "Nature of Work",
            "type": "textarea",
            "required": True,
            "validation": {"min_length": 10, "max_length": 500},
            "placeholder": "Describe the work assigned",
            "step": 4,
            "section": "engagement"
        },
        {
            "field_id": "expected_duration_days",
            "label": "Expected Duration (Days)",
            "type": "number",
            "required": False,
            "validation": {"min": 1, "max": 365},
            "step": 4,
            "section": "engagement"
        }
    ],
    
    EmploymentType.DEPUTATION: [
        {
            "field_id": "parent_department",
            "label": "Parent Department",
            "type": "select",
            "required": True,
            "master_ref": "departments",
            "placeholder": "Department from which deputed",
            "step": 4,
            "section": "deputation"
        },
        {
            "field_id": "parent_designation",
            "label": "Designation in Parent Dept.",
            "type": "text",
            "required": True,
            "placeholder": "Substantive post held",
            "step": 4,
            "section": "deputation"
        },
        {
            "field_id": "deputation_order_no",
            "label": "Deputation Order Number",
            "type": "text",
            "required": True,
            "placeholder": "e.g., DEP/2024/001",
            "step": 4,
            "section": "deputation"
        },
        {
            "field_id": "deputation_start_date",
            "label": "Deputation Start Date",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "deputation"
        },
        {
            "field_id": "deputation_end_date",
            "label": "Deputation End Date",
            "type": "date",
            "required": True,
            "validation": {"must_be_after": "deputation_start_date"},
            "step": 4,
            "section": "deputation"
        },
        {
            "field_id": "lien_retained",
            "label": "Lien Retained",
            "type": "select",
            "required": True,
            "options": [
                {"value": "YES", "label": "Yes - Lien retained in parent department"},
                {"value": "NO", "label": "No - Lien surrendered"}
            ],
            "default": "YES",
            "step": 4,
            "section": "deputation"
        },
        {
            "field_id": "deputation_allowance_percentage",
            "label": "Deputation Allowance (%)",
            "type": "number",
            "required": False,
            "default": 10,
            "validation": {"min": 0, "max": 25},
            "step": 4,
            "section": "deputation"
        }
    ],
    
    EmploymentType.REEMPLOYED: [
        {
            "field_id": "previous_retirement_order_no",
            "label": "Previous Retirement Order No.",
            "type": "text",
            "required": True,
            "placeholder": "e.g., RET/2023/001",
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "retirement_date",
            "label": "Date of Retirement",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "previous_designation",
            "label": "Previous Designation",
            "type": "text",
            "required": True,
            "placeholder": "Last held post before retirement",
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "reemployment_order_no",
            "label": "Re-employment Order No.",
            "type": "text",
            "required": True,
            "placeholder": "e.g., REEMP/2024/001",
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "reemployment_start_date",
            "label": "Re-employment Start Date",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "reemployment_end_date",
            "label": "Re-employment End Date",
            "type": "date",
            "required": True,
            "validation": {"must_be_after": "reemployment_start_date"},
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "last_pay_drawn",
            "label": "Last Pay Drawn (₹)",
            "type": "number",
            "required": True,
            "validation": {"min": 0},
            "placeholder": "Basic pay at retirement",
            "step": 4,
            "section": "reemployment"
        },
        {
            "field_id": "pension_received",
            "label": "Monthly Pension (₹)",
            "type": "number",
            "required": True,
            "validation": {"min": 0},
            "placeholder": "Current pension amount",
            "step": 4,
            "section": "reemployment"
        }
    ],
    
    EmploymentType.OUTSOURCED: [
        {
            "field_id": "vendor_name",
            "label": "Vendor/Agency Name",
            "type": "text",
            "required": True,
            "placeholder": "Name of outsourcing agency",
            "step": 4,
            "section": "outsourcing"
        },
        {
            "field_id": "vendor_contract_no",
            "label": "Vendor Contract Number",
            "type": "text",
            "required": True,
            "placeholder": "Agency's contract reference",
            "step": 4,
            "section": "outsourcing"
        },
        {
            "field_id": "contract_start_date",
            "label": "Contract Start Date",
            "type": "date",
            "required": True,
            "step": 4,
            "section": "outsourcing"
        },
        {
            "field_id": "contract_end_date",
            "label": "Contract End Date",
            "type": "date",
            "required": True,
            "validation": {"must_be_after": "contract_start_date"},
            "step": 4,
            "section": "outsourcing"
        },
        {
            "field_id": "role_description",
            "label": "Role Description",
            "type": "textarea",
            "required": True,
            "validation": {"min_length": 10, "max_length": 500},
            "placeholder": "Describe assigned responsibilities",
            "step": 4,
            "section": "outsourcing"
        },
        {
            "field_id": "reporting_officer",
            "label": "Reporting Officer",
            "type": "text",
            "required": False,
            "placeholder": "Name of supervising officer",
            "step": 4,
            "section": "outsourcing"
        }
    ]
}

# ==================== FIELDS TO REJECT (SERVICE BOOK ONLY) ====================
# These fields belong ONLY in the Service Book, NOT in Employee Profile.
# Any attempt to include these in profile creation/update will be rejected.

REJECTED_FIELDS = [
    # Pay-related fields (Service Book Part II-B)
    "pay_scale",
    "pay_level",
    "basic_pay",
    "grade_pay",
    "current_pay",
    "increment_date",
    "next_increment_date",
    "increment_history",
    "pay_fixation_date",
    "pay_fixation_order",
    "da_percentage",
    "hra_percentage",
    "total_emoluments",
    "gross_salary",
    "net_salary",
    
    # Historical promotion/transfer (Service Book Part II-A)
    "promotion_date",
    "promotion_order_number",
    "transfer_history",
    "posting_history",
    "appointment_date",           # Use Service Book Part II-A APPOINTMENT event
    "confirmation_date",          # Use Service Book Part II-A CONFIRMATION event
    "previous_postings",
    "previous_designations",
    
    # Leave-related (Service Book Part III - calculated from transactions)
    "leave_balance",
    "earned_leave_balance",
    "half_pay_leave_balance",
    "casual_leave_balance",
    "leave_encashment_history",
    "ltc_availed",
    
    # Disciplinary (Service Book Part IV)
    "disciplinary_case",
    "suspension_details",
    "penalty_history",
    "charge_sheet_history",
    
    # MACP/ACP (Service Book Part II-B)
    "macp_acp",
    "macp_date",
    "acp_date",
    "financial_upgradation_history",
    
    # Retirement/Pension (Service Book Part V)
    "pension_amount",
    "gratuity_amount",
    "qualifying_service",
    "ppo_number",
    
    # PCF/NPS (managed via Service Book)
    "gpf_balance",
    "pcf_account_number",
    "nps_pran",
    "nps_corpus",
    
    # Annual increment
    "annual_increment",
    "stagnation_increment",
]

# ==================== WIZARD STEPS CONFIGURATION ====================

WIZARD_STEPS = [
    {
        "step": 1,
        "title": "Personal Information",
        "description": "Basic personal details",
        "sections": ["identification", "personal"],
        "icon": "User"
    },
    {
        "step": 2,
        "title": "Contact & Address",
        "description": "Contact information and addresses",
        "sections": ["contact", "address"],
        "icon": "MapPin"
    },
    {
        "step": 3,
        "title": "Employment Details",
        "description": "Department, office, and employment type",
        "sections": ["posting", "employment"],
        "icon": "Building2"
    },
    {
        "step": 4,
        "title": "Type-Specific Details",
        "description": "Details based on employment type",
        "sections": ["appointment", "contract", "engagement", "deputation", "reemployment", "outsourcing", "service"],
        "dynamic": True,
        "icon": "FileText"
    },
    {
        "step": 5,
        "title": "Review & Submit",
        "description": "Review all information before submission",
        "sections": [],
        "is_review": True,
        "icon": "CheckCircle2"
    }
]

# ==================== VALIDATION RULES ====================

def get_fields_for_employment_type(employment_type: str) -> List[Dict]:
    return employee_form_validation.get_fields_for_employment_type(
        employment_type,
        common_fields=COMMON_FIELDS,
        employment_type_fields=EMPLOYMENT_TYPE_FIELDS,
        employment_type_enum=EmploymentType,
    )

def get_allowed_field_ids(employment_type: str) -> List[str]:
    return employee_form_validation.get_allowed_field_ids(
        employment_type,
        common_fields=COMMON_FIELDS,
        employment_type_fields=EMPLOYMENT_TYPE_FIELDS,
        employment_type_enum=EmploymentType,
    )

def validate_submission(employment_type: str, data: Dict) -> Dict:
    return employee_form_validation.validate_submission(
        employment_type,
        data,
        common_fields=COMMON_FIELDS,
        employment_type_fields=EMPLOYMENT_TYPE_FIELDS,
        employment_type_enum=EmploymentType,
        rejected_fields=REJECTED_FIELDS,
    )

# ==================== FORM SCHEMA EXPORT ====================

EMPLOYEE_FORM_SCHEMA = {
    "form_id": "employee_profile_wizard",
    "title": "Employee Profile",
    "version": "2.0.0",
    "compliance": "IEMS",
    "common_fields": COMMON_FIELDS,
    "employment_type_fields": {k.value: v for k, v in EMPLOYMENT_TYPE_FIELDS.items()},
    "rejected_fields": REJECTED_FIELDS,
    "wizard_steps": WIZARD_STEPS,
    "validation_note": "Employee Profile stores identity + current engagement. All historical/financial data belongs to Service Book."
}
