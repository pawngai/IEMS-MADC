# Domain Separation Schema Definitions
# =====================================
#
# This module defines the STRICT boundary between Profile and Service Book domains.
# Any field listed in one domain MUST NOT appear in the other domain's payload.

from typing import Set, Dict, List

# ==================== PROFILE FIELDS (MUTABLE IDENTITY) ====================
# These fields belong ONLY to the Employee Profile domain

PROFILE_FIELDS: Set[str] = {
    # System identifiers
    "employee_id",
    "employee_code",
    
    # Personal identity (IMMUTABLE after verification)
    "full_name",
    "gender",
    "date_of_birth",
    "father_name",
    "father_husband_name",
    "mother_name",
    "nationality",
    "category",
    "sub_caste",
    "caste",
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
    "group",
    "service",
    "mode_of_recruitment",

    # Employment classification
    "employment_type",
    "employment_type_code",
    "date_of_initial_engagement",
    
    # Current assignment (IDs only - NOT historical)
    "current_department_id",
    "current_designation_id",
    "current_office_id",
    "department_id",
    "designation_id",
    "office_id",
    "department_code",
    "designation_code",
    "office_code",
    "reporting_officer_id",
    
    # Status
    "employee_status",
    "is_active",
    "workflow_status",
    "status_remarks",
    "status_effective_date",
    
    # Workflow tracking
    "verified_by",
    "verified_at",
    "approved_by",
    "approved_at",
    "locked_by",
    "locked_at",
    "workflow_remarks",

    # ESS tracking
    "employee_section_completed",
    "data_entry_section_completed",
    
    # Contact details (ESS editable)
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
    "permanent_address",
    "present_address",
    "correspondence_address",
    
    # Embedded objects
    "contact",
    "identifiers",
    
    # Emergency contact
    "emergency_name",
    "emergency_phone",
    "emergency_relation",
    
    # Identity documents
    "aadhaar_number",
    "pan_number",
    
    # Photo
    "photo_url",
    "signature_url",
    "thumb_impression_url",
    "photo",
    "photo_updated_at",
    
    # Type-specific appointment fields (belongs in PROFILE for initial creation)
    "appointment_order_no",
    "appointment_order_date",
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
    "cadre",
    "pay_level",
    "probation_period_months",
    "basic_pay",
}

# ==================== SERVICE BOOK FIELDS (IMMUTABLE LEDGER) ====================
# These fields belong ONLY to the Service Book domain

SERVICE_BOOK_FIELDS: Set[str] = {
    # Entry identifiers
    "entry_id",
    "sequence_number",
    "chain_sequence",
    
    # Event classification
    "event_type",
    "event_category",
    "part",  # I, II-A, II-B, III, IV, V
    
    # Effective dates
    "effective_from",
    "effective_to",
    "effective_date",
    
    # Order details
    "order_number",
    "order_date",
    "order_reference",
    "authority",
    "issued_by",
    "sanctioning_authority",
    
    # Pay events (Service Book ONLY)
    "pay_scale",
    "pay_band",
    "grade_pay",
    "pay_matrix_level",
    "pay_matrix_cell",
    "increment_amount",
    "increment_date",
    "arrears_amount",
    "dearness_allowance",
    "house_rent_allowance",
    "total_emoluments",
    
    # Leave events (Service Book ONLY)
    "leave_type",
    "leave_from",
    "leave_to",
    "leave_days",
    "leave_balance",
    "leave_credit_type",
    "leave_encashment_days",
    "leave_encashment_amount",
    "earned_leave_balance",
    "half_pay_leave_balance",
    "commuted_leave_balance",
    "leave_not_due_balance",
    
    # Promotion/Transfer events
    "from_designation",
    "to_designation",
    "from_department",
    "to_department",
    "from_office",
    "to_office",
    "from_pay_level",
    "to_pay_level",
    "promotion_type",
    "transfer_type",
    
    # Disciplinary events
    "charge_sheet_number",
    "suspension_order",
    "penalty_type",
    "penalty_details",
    "appeal_status",
    "reinstatement_order",
    
    # Retirement events
    "retirement_type",
    "superannuation_date",
    "pension_order",
    "pension_amount",
    "gratuity_amount",
    "commutation_amount",
    "encashment_amount",
    "ppo_number",
    
    # Hash chain integrity
    "entry_hash",
    "previous_entry_hash",
    
    # Correction fields
    "corrects_entry_id",
    "correction_reason",
    "correction_type",
    "is_corrected",
    "is_correction",
    "superseded_by",
    "corrected_by_entry_id",
    
    # Workflow and status
    "entry_status",
    "status",
    "attestation_status",
    "attested_by",
    "attested_at",
    "attestation_remarks",
    
    # Workflow tracking fields
    "submitted_by",
    "submitted_at",
    "verified_by",
    "verified_at",
    "verification_remarks",
    "approved_by",
    "approved_at",
    "approval_remarks",
    "rejected_by",
    "rejected_at",
    "rejection_reason",
    "issuing_office",
    
    # Employee reference
    "employee_id",
    
    # Attachments
    "attachments",
    "supporting_documents",
    
    # Payload for event-specific data
    "payload",
    "remarks",
    "name_in_block_letters",
    "parent_name",
    "caste_category",
    "date_of_birth_christian",
    "phone_number",
    "email",
    "permanent_address",
    "present_address",
    "emergency_contact",
    "medical_fitness_certificate",
    "medical_exam_date",
    "medical_officer_name",
    "medical_category",
    "character_verification_done",
    "character_verification_date",
    "character_verification_authority",
    "police_verification_done",
    "police_verification_date",
    "oath_of_allegiance_date",
    "oath_of_secrecy_date",
    "marital_status_declaration_date",
    "declared_hometown",
    "hometown_declaration_date",
    "initial_property_return_date",
    "entries_confirmed",
    "family_members",
    "pcf_account_number",
    "pcf_nominee_name",
    "pcf_nominee_relation",
    "pcf_nominee_share_percent",
    "pcf_nomination",
    "dcr_gratuity_nomination",
    "gratuity_nominee_name",
    "gratuity_nominee_relation",
    "gratuity_nominee_share_percent",
    "family_pension_nomination",
    "leave_encashment_nomination",
    "nps_pran_number",
    "nps_nomination",
    "bank_account_number",
    "bank_name",
    "bank_ifsc",
    "previous_services",
    "total_previous_qualifying_service",
    "foreign_services",
    "part_iii_verified",
    "part_iii_verified_by",
    "part_iii_verification_date",
    "verified",
    "verification_date",
}

# ==================== FORBIDDEN IN PROFILE ====================
# These fields MUST NEVER appear in Profile API payloads

FORBIDDEN_IN_PROFILE: Set[str] = {
    # Core Service Book fields
    "entry_id",
    "event_type",
    "event_category",
    "effective_from",
    "effective_to",
    "entry_hash",
    "previous_entry_hash",
    "chain_sequence",
    "corrects_entry_id",
    "correction_reason",
    "is_corrected",
    "superseded_by",
    "entry_status",
    "attestation_status",
    "attested_by",
    "attested_at",
    
    # Pay data (belongs in Service Book)
    "pay_scale",
    "pay_band",
    "grade_pay",
    "pay_matrix_level",
    "pay_matrix_cell",
    "increment_amount",
    "increment_date",
    "arrears_amount",
    "dearness_allowance",
    "house_rent_allowance",
    "total_emoluments",
    
    # Leave balances (derived from Service Book)
    "leave_balance",
    "earned_leave_balance",
    "half_pay_leave_balance",
    "commuted_leave_balance",
    "leave_not_due_balance",
    "leave_type",
    "leave_from",
    "leave_to",
    "leave_days",
    
    # Historical/transition data (belongs in Service Book)
    "from_designation",
    "to_designation",
    "from_department",
    "to_department",
    "from_office",
    "to_office",
    "from_pay_level",
    "to_pay_level",
    "promotion_type",
    "transfer_type",
    "promotion_date",
    "transfer_date",
    "posting_history",
    "promotion_history",
    
    # Disciplinary records (belongs in Service Book)
    "charge_sheet_number",
    "suspension_order",
    "penalty_type",
    "penalty_details",
    "appeal_status",
    "reinstatement_order",
    
    # Retirement records (belongs in Service Book)
    "pension_order",
    "pension_amount",
    "gratuity_amount",
    "commutation_amount",
    "ppo_number",
    "pcf_account_number",
    "pcf_nominee_name",
    "pcf_nominee_relation",
    "pcf_nominee_share_percent",
    "pcf_nomination",
    "pcf_nominations",
    "gpf_nominee_name",
    "gpf_nominee_relation",
    "gpf_nominee_share_percent",
    "gpf_nominations",
    "gpf_nomination",
    "gratuity_nominee_name",
    "gratuity_nominee_relation",
    "gratuity_nominee_share_percent",
    "gratuity_nominations",
    "gpf_account_number",
    "nps_pran_number",
    "bank_account_number",
    "bank_name",
    "bank_ifsc",
    "family_members",
    "previous_services",
    "total_previous_qualifying_service",
    "foreign_services",
    "part_iii_verified",
    "part_iii_verified_by",
    "part_iii_verification_date",
}

# ==================== FORBIDDEN IN SERVICE BOOK ====================
# These fields MUST NEVER appear in Service Book API payloads

FORBIDDEN_IN_SERVICE_BOOK: Set[str] = {
    # Profile identity fields (already stored in Profile)
    "full_name",
    "gender",
    "date_of_birth",
    "category",
    # Contact details (ESS domain)
    "mobile_primary",
    "mobile_alternate",
    "email_personal",
    "correspondence_address",
    "emergency_name",
    "emergency_phone",
    
    # Identity documents (Profile domain)
    "aadhaar_number",
    "pan_number",
    
    # Photo
    "photo_url",
    "photo",
}

# ==================== EMPLOYMENT TYPE RULES ====================
# Defines which fields are required/allowed for each employment type

PROFILE_EMPLOYMENT_TYPE_RULES: Dict[str, Dict[str, List[str]]] = {
    "REGULAR": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
        ],
        "optional": [
            "appointment_order_no",
            "appointment_order_date",
            "cadre",
            "pay_level",
            "probation_period_months",
            "basic_pay",
        ],
        "forbidden": [
            "contract_end_date",
            "consolidated_pay",
            "daily_wage_rate",
            "muster_roll_number",
            "parent_department",
            "lien_status",
            "agency_name",
        ],
    },
    "CONTRACTUAL": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
            "contract_start_date",
            "contract_end_date",
        ],
        "optional": [
            "contract_order_no",
            "consolidated_pay",
            "contract_authority",
            "vendor_agency",
            "renewal_allowed",
        ],
        "forbidden": [
            "cadre",
            "pension_scheme",
            "probation_period_months",
            "daily_wage_rate",
            "parent_department",
            "lien_status",
        ],
    },
    "CONTRACT": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
            "current_designation_id",
            "engagement_order_no",
            "engagement_end_date",
            "fixed_monthly_amount",
        ],
        "optional": [
            "engagement_order_date",
            "document_ids",
            "engagement_remarks",
        ],
        "forbidden": [
            "daily_wage_rate",
            "muster_roll_number",
            "pay_level",
            "basic_pay",
        ],
    },
    "MUSTER_ROLL": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
            "current_designation_id",
            "engagement_order_no",
            "daily_wage_rate",
        ],
        "optional": [
            "engagement_order_date",
            "wage_rate_unit",
            "document_ids",
            "engagement_remarks",
        ],
        "forbidden": [
            "fixed_monthly_amount",
            "pay_level",
            "basic_pay",
            "contract_end_date",
        ],
    },
    "FIXED_PAY": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
            "current_designation_id",
            "engagement_order_no",
            "fixed_monthly_amount",
        ],
        "optional": [
            "engagement_order_date",
            "document_ids",
            "engagement_remarks",
        ],
        "forbidden": [
            "daily_wage_rate",
            "muster_roll_number",
            "pay_level",
            "basic_pay",
        ],
    },
    "CO_TERMINUS": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
            "current_designation_id",
            "engagement_order_no",
            "pay_level",
            "basic_pay",
        ],
        "optional": [
            "engagement_order_date",
            "document_ids",
            "engagement_remarks",
        ],
        "forbidden": [
            "daily_wage_rate",
            "muster_roll_number",
            "fixed_monthly_amount",
        ],
    },
    "WAGES": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "current_department_id",
            "current_designation_id",
            "daily_wage_rate",
        ],
        "optional": [
            "wage_rate_unit",
            "document_ids",
            "engagement_remarks",
        ],
        "forbidden": [
            "fixed_monthly_amount",
            "pay_level",
            "basic_pay",
            "contract_end_date",
        ],
    },
    "DAILY_WAGE": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
        ],
        "optional": [
            "engagement_order_no",
            "muster_roll_number",
            "daily_wage_rate",
            "engagement_office",
            "nature_of_work",
            "expected_duration_days",
        ],
        "forbidden": [
            "cadre",
            "pay_level",
            "contract_end_date",
            "parent_department",
            "lien_status",
        ],
    },
    "DEPUTATION": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "parent_department",
            "deputation_start_date",
        ],
        "optional": [
            "deputation_order_no",
            "parent_designation",
            "lien_status",
            "deputation_end_date",
            "deputation_allowance_percent",
        ],
        "forbidden": [
            "daily_wage_rate",
            "muster_roll_number",
            "contract_end_date",
            "agency_name",
        ],
    },
    "OUTSOURCED": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
            "agency_name",
        ],
        "optional": [
            "outsourcing_order_no",
            "agency_contract_number",
            "sla_reference",
            "contract_start_date",
            "contract_end_date",
            "monthly_billing_rate",
            "role_description",
        ],
        "forbidden": [
            "cadre",
            "pay_level",
            "probation_period_months",
            "parent_department",
            "lien_status",
            "daily_wage_rate",
        ],
    },
    "REEMPLOYED": {
        "required": [
            "full_name",
            "date_of_birth",
            "gender",
            "employment_type",
            "date_of_initial_engagement",
        ],
        "optional": [
            "previous_retirement_date",
            "reemployment_start_date",
            "pension_details",
        ],
        "forbidden": [
            "daily_wage_rate",
            "muster_roll_number",
            "agency_name",
        ],
    },
}

# ==================== SERVICE BOOK EVENT TYPE RULES ====================
# Defines which fields are required for each event type

SERVICE_BOOK_EVENT_TYPE_RULES: Dict[str, Dict[str, List[str]]] = {
    "APPOINTMENT": {
        "required": ["employee_id", "event_type", "effective_from", "order_number", "order_date"],
        "optional": ["authority", "remarks", "attachments", "payload"],
        "payload_fields": ["employment_type", "department_id", "designation_id"],
    },
    "PROMOTION": {
        "required": ["employee_id", "event_type", "effective_from", "order_number", "order_date"],
        "optional": ["authority", "remarks", "attachments"],
        "payload_fields": ["from_designation", "to_designation", "from_pay_level", "to_pay_level"],
    },
    "TRANSFER": {
        "required": ["employee_id", "event_type", "effective_from", "order_number", "order_date"],
        "optional": ["authority", "remarks"],
        "payload_fields": ["from_office", "to_office", "transfer_type"],
    },
    "PAY_FIXATION": {
        "required": ["employee_id", "event_type", "effective_from", "order_number", "order_date"],
        "optional": ["authority", "remarks"],
        "payload_fields": ["pay_level", "pay_matrix_cell", "basic_pay", "arrears_amount"],
    },
    "ANNUAL_INCREMENT": {
        "required": ["employee_id", "event_type", "effective_from"],
        "optional": ["order_number", "remarks"],
        "payload_fields": ["increment_amount", "new_basic_pay"],
    },
    "LEAVE_CREDIT": {
        "required": ["employee_id", "event_type", "effective_from"],
        "optional": ["remarks"],
        "payload_fields": ["leave_type", "credit_days", "new_balance"],
    },
    "LEAVE_DEBIT": {
        "required": ["employee_id", "event_type", "effective_from", "order_number"],
        "optional": ["remarks"],
        "payload_fields": ["leave_type", "leave_from", "leave_to", "days", "balance_after"],
    },
    "SUSPENSION": {
        "required": ["employee_id", "event_type", "effective_from", "order_number", "order_date"],
        "optional": ["remarks"],
        "payload_fields": ["suspension_order", "charge_sheet_number"],
    },
    "RETIREMENT": {
        "required": ["employee_id", "event_type", "effective_from", "order_number", "order_date"],
        "optional": ["authority", "remarks"],
        "payload_fields": ["retirement_type", "pension_order"],
    },
    "SUPERSESSION": {
        "required": ["employee_id", "event_type", "effective_from", "corrects_entry_id", "correction_reason"],
        "optional": ["authority", "remarks"],
        "payload_fields": ["corrected_fields"],
    },
}
