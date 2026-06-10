# Current Fields Inventory — employee_identity & employee_profile

Generated: 2026-06-11 (Phase 0, refactor to context-minimized architecture)

This enumerates **every** schema/model field currently defined in the
`employee_identity` and `employee_profile` backend contexts, plus the flat
upsert/policy field surface that the write API accepts and persists. No field
here may be dropped during the merge into `employee_master`; see
[employee_identity_profile_field_mapping.md](employee_identity_profile_field_mapping.md)
for the destination of each.

Legend — Req: R = required, O = optional. Status: KEEP = stays canonical,
MAP = renamed/moved with mapping, LEGACY = preserved under `legacy_fields`.

---

## 1. employee_identity context

### 1.1 `EmployeeIdentity` (canonical identity document)
Source: `backend/contexts/employee_identity/schemas/identity_model.py`
Collection: canonical employee identity.

| Field | Type | Req | Validation / Default | New owner | Status |
|---|---|---|---|---|---|
| id | str | R | uuid4 default | employee_master | KEEP |
| employee_id | str | R | uuid4 default; cross-context join key | employee_master | KEEP |
| employee_code | str? | O | formatted via `format_employee_code` | employee_master | KEEP |
| full_name | str | R | min 2, max 100 | employee_master | KEEP |
| gender | Gender enum | R | Male/Female/Other | employee_master | KEEP |
| date_of_birth | str | R | `YYYY-MM-DD` validated | employee_master | KEEP |
| mobile_primary | str? | O | indian mobile (in command) | employee_master | KEEP |
| email_official | str? | O | email normalized (in command) | employee_master | KEEP |
| employee_status | EmployeeStatus enum | R | default ACTIVE | employee_master | KEEP |
| status_effective_date | str? | O | date | employee_master | KEEP |
| status_remarks | str? | O | — | employee_master | KEEP |
| created_at | str | R | iso default | employee_master | KEEP |
| created_by | str? | O | — | employee_master | KEEP |
| updated_at | str | R | iso default | employee_master | KEEP |
| updated_by | str? | O | — | employee_master | KEEP |
| version | int | R | default 1 | employee_master | KEEP |

### 1.2 `EmployeeIdentityCreate` (write command)
Source: `employee_identity/schemas/commands.py` (`extra="forbid"`)

Adds **appointment-time assignment** fields not stored on the bare identity doc
but accepted at creation and projected into the composed view:

| Field | Type | Req | Validation | New owner | Status |
|---|---|---|---|---|---|
| current_designation_id | str? | O | — | employee_master (current assignment) | KEEP |
| current_office_id | str? | O | — | employee_master (current assignment) | KEEP |
| reporting_officer_id | str? | O | — | employee_master (current assignment) | KEEP |

`EmployeeIdentityUpdate` accepts the same set (all optional).

### 1.3 `DATA_ENTRY_EDITABLE_FIELDS` (identity field policy)
Source: `employee_identity/schemas/field_policies.py` — policy set, not new data:
`full_name, gender, date_of_birth, current_designation_id, current_office_id,
reporting_officer_id, employee_status, status_effective_date, status_remarks`.
→ Carried to `employee_master/schemas/field_policies.py` unchanged.

### 1.4 Enums
Source: `employee_identity/schemas/enums.py` + `employee_profile/schemas/profile_model.py`
- `Gender`: Male, Female, Other
- `EmployeeStatus`: ACTIVE, INACTIVE, DUPLICATE, MERGED, ARCHIVED
- `EmploymentType`: REGULAR, PROBATIONER, TEMPORARY, CONTRACTUAL, DAILY_WAGE,
  REEMPLOYED, OUTSOURCED, MUSTER_ROLL, CONTRACT, FIXED_PAY, WAGES, DAILY_RATED,
  CO_TERMINUS, DEPUTATION, CASUAL, PART_TIME
- `WorkflowStatus`: DRAFT, SUBMITTED, VERIFIED, APPROVED, ACTIVE, ATTESTED,
  LOCKED, REJECTED, SUPERSEDED

→ All enums move verbatim to `employee_master/schemas/enums.py` (KEEP).

---

## 2. employee_profile context

### 2.1 `EmployeeIdentity` snapshot (profile-side composed identity)
Source: `employee_profile/schemas/profile_model.py`

Superset of 1.1 adding the projected appointment/assignment facts:

| Field | Type | Req | New owner | Status |
|---|---|---|---|---|
| aadhaar_number | str? | O | employee_master (`identifiers.aadhaar_number`) | MAP |
| employment_type | EmploymentType | R | employee_master | KEEP |
| date_of_initial_engagement | str | R | employee_master (appointment-time) | KEEP |
| current_department_id | str | R | employee_master (current assignment); FK → organization_master | KEEP |
| current_designation_id | str? | O | employee_master; FK → organization_master | KEEP |
| current_office_id | str? | O | employee_master; FK → organization_master | KEEP |
| reporting_officer_id | str? | O | employee_master | KEEP |
| *(all 1.1 fields)* | | | employee_master | KEEP |

### 2.2 `EmployeeProfileExtension` (employee-owned enrichment)
Source: `employee_profile/schemas/profile_model.py`

| Field | Type | Req | Default/Validation | New owner | Status |
|---|---|---|---|---|---|
| id | str | R | uuid4 | employee_master | KEEP |
| employee_id | str | R | join key | employee_master | KEEP |
| father_name | str? | O | max 100 | employee_master | KEEP |
| mother_name | str? | O | max 100 | employee_master | KEEP |
| nationality | str | R | default "Indian", max 50 | employee_master | KEEP |
| category | str? | O | reservation category | employee_master | KEEP |
| sub_caste | str? | O | — | employee_master | KEEP |
| religion | str? | O | — | employee_master | KEEP |
| date_of_birth_saka | str? | O | — | employee_master | KEEP |
| place_of_birth | str? | O | — | employee_master | KEEP |
| blood_group | str? | O | — | employee_master | KEEP |
| height_cm | float? | O | — | employee_master | KEEP |
| identification_marks | List[str] | R | default [] | employee_master | KEEP |
| marital_status | str? | O | — | employee_master | KEEP |
| spouse_name | str? | O | — | employee_master | KEEP |
| educational_qualifications_initial | List[dict] | R | default [] | employee_master | KEEP |
| educational_qualifications_acquired | List[dict] | R | default [] | employee_master | KEEP |
| professional_qualifications | List[dict] | R | default [] | employee_master | KEEP |
| contact | ContactDetails | R | default factory | employee_master (embedded) | KEEP |
| identifiers | IdentityDocuments? | O | — | employee_master (embedded) | KEEP |
| photo_url | str? | O | media | employee_master (refs app_platform/documents storage) | KEEP |
| photo_updated_at | str? | O | — | employee_master | KEEP |
| signature_url | str? | O | media | employee_master | KEEP |
| thumb_impression_url | str? | O | media | employee_master | KEEP |
| workflow_status | WorkflowStatus | R | default DRAFT | employee_master (status) / workflow (process) | KEEP |
| workflow_remarks | str? | O | — | employee_master | KEEP |
| employee_section_completed | bool | R | default False | employee_master | KEEP |
| data_entry_section_completed | bool | R | default False | employee_master | KEEP |
| created_at/created_by | str/str? | R/O | — | employee_master | KEEP |
| updated_at/updated_by | str/str? | R/O | — | employee_master | KEEP |
| verified_at/verified_by | str?/str? | O | — | employee_master | KEEP |
| approved_at/approved_by | str?/str? | O | — | employee_master | KEEP |
| locked_at/locked_by | str?/str? | O | — | employee_master | KEEP |
| version | int | R | default 1 | employee_master | KEEP |

### 2.3 `ContactDetails` (embedded value object)
Sources: `profile_model.py` **and** `employee_identity/schemas/value_objects.py`
(two definitions — must be unified).

Stored nested fields: `mobile_primary, mobile_alternate, email_personal,
email_official, address, city, district, state, pincode, present_address,
present_city, present_district, present_state, present_pincode, emergency_name,
emergency_phone, emergency_relation`.
Validation: mobile `^[6-9]\d{9}$`, pincode `^\d{6}$`.
→ employee_master embedded `contact`. **KEEP**.

⚠ **Mapping conflict:** the write path (`update_profile_extension.CONTACT_FIELDS`)
accepts `address_line1` / `address_line2` / `present_address_line1` /
`present_address_line2` and writes them to `contact.address_line1` etc., but the
`ContactDetails` model declares only `address` / `present_address`. See mapping
doc — these must be reconciled (MAP `address_line1`+`address_line2` ↔ `address`)
or preserved under `contact.legacy_fields`.

### 2.4 `IdentityDocuments` (embedded value object)
`aadhaar_number` (`^\d{12}$`), `pan_number` (`^[A-Z]{5}\d{4}[A-Z]$`, upper-cased).
→ employee_master embedded `identifiers`. **KEEP**.

### 2.5 Employment-type-specific fields (flat, accepted by `EmployeeProfileExtensionUpsert`)
Source: `employee_profile/schemas/commands.py` + `field_policies.PROFILE_EXTENSION_EDITABLE_FIELDS`.
Accepted by the write API and persisted as **top-level fields on the profile
document** (via `extension_updates` `$set`), though **not declared** in
`EmployeeProfileExtension`. **All must be preserved** (declare in employee_master
or store under `legacy_fields`):

`contract_order_no, contract_start_date, contract_end_date, consolidated_pay,
contract_authority, vendor_agency, renewal_allowed, engagement_order_no,
engagement_order_date, engagement_end_date, remuneration_type,
muster_roll_number, daily_wage_rate, wage_rate_unit, engagement_office,
nature_of_work, expected_duration_days, fixed_monthly_amount, basic_pay,
pay_level, document_ids, engagement_remarks, deputation_order_no,
parent_department, parent_designation, lien_status, deputation_start_date,
deputation_end_date, deputation_allowance_percent, outsourcing_order_no,
agency_name, agency_contract_number, sla_reference, monthly_billing_rate,
role_description`

Note: pay-figure fields (`basic_pay, pay_level, consolidated_pay,
daily_wage_rate, fixed_monthly_amount, monthly_billing_rate`) are
**appointment-time facts**, not ledger entries → stay in employee_master.
pay_benefits may later project from them, but they are NOT moved.

### 2.6 ESS-editable subset
`EmployeeProfileExtensionESSUpdate` / `ESS_EDITABLE_FIELDS` is a permission subset
of the above plus `gender`. No new fields. → policy carried to employee_master.

### 2.7 Response / audit models
- `EmployeeProfileResponse` (directory row): employee_id, employee_code,
  full_name, gender, date_of_birth, employment_type, date_of_initial_engagement,
  current_department_id, current_designation_id, current_office_id,
  employee_status, workflow_status, employee_section_completed, photo_url,
  created_at, updated_at → becomes `EmployeeDirectoryItem`.
- `EmployeeCompositeProfileResponse` adds data_entry_section_completed,
  workflow_remarks → basis for `EmployeeMasterResponse`.
- `ProfileAuditLog`: id, employee_id, action, performed_by_id/name/role,
  previous_data, new_data, changed_fields, workflow_status_before/after, remarks,
  ip_address, user_agent, timestamp, integrity_hash → audit concern; remains
  emitted to `app_platform/audit` (no field loss).

---

## 3. Field-count reconciliation target

| Group | Distinct fields |
|---|---|
| Identity core (1.1 + 1.2) | 19 |
| Profile snapshot extras (2.1) | 7 |
| Profile extension (2.2) | 36 |
| Contact embedded (2.3) | 17 (+4 line1/line2 variants) |
| Identifiers embedded (2.4) | 2 |
| Employment-type flat (2.5) | 35 |

The migration report (Phase 9) must show every one of these present in
`EmployeeMasterSnapshot` or under `legacy_fields`, with **0 unmapped**.
