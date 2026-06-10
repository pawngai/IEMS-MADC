# Field Mapping — employee_identity + employee_profile → employee_master

Generated: 2026-06-11 (Phase 0)

Canonical target models (Phase 1):
`EmployeeMasterCreate`, `EmployeeMasterUpdate`, `EmployeeMasterResponse`,
`EmployeeMasterSnapshot`, `EmployeeDirectoryItem`.

Rule: every old field → (1) same canonical name, (2) mapped name (documented), or
(3) `legacy_fields[...]` with a migration note. **Nothing is dropped.**

---

## A. Direct carry (old name == new name) — Status KEEP

All fields in inventory §1.1, §1.2, §2.1, §2.2, §2.4 keep their exact names in
`EmployeeMasterSnapshot`. The composed snapshot is the union of the identity doc
and the profile extension, which is already what `EmployeeCompositeProfileView`
represents today — so this is a rename of the *container*, not the fields.

```
EmployeeMasterSnapshot  ⊇  EmployeeIdentity(identity) ∪ EmployeeProfileExtension
EmployeeMasterResponse  ≅  EmployeeCompositeProfileResponse
EmployeeDirectoryItem   ≅  EmployeeProfileResponse
EmployeeMasterCreate    ≅  EmployeeIdentityCreate           (identity-first, extra="forbid")
EmployeeMasterUpdate    ≅  EmployeeIdentityUpdate ∪ EmployeeProfileExtensionUpsert
```

## B. Renamed / reconciled fields — Status MAP

| Old name(s) | Old location | New canonical name | Note |
|---|---|---|---|
| `aadhaar_number` (top-level on profile snapshot) | profile_model.EmployeeIdentity | `identifiers.aadhaar_number` | already also embedded; collapse to single embedded location |
| `address_line1` + `address_line2` | write path `contact.*` | `contact.address` | join with newline OR keep both as `contact.address_line1/2`; **decision: keep line1/line2 as canonical, derive `address` for back-compat read** |
| `present_address_line1` + `present_address_line2` | write path `contact.*` | `contact.present_address` | same treatment |
| `EmployeeProfileResponse` | responses.py | `EmployeeDirectoryItem` | container rename only |
| `EmployeeCompositeProfileResponse` | responses.py | `EmployeeMasterResponse` | container rename only |
| `EmployeeCompositeProfileView` | profile_model.py | `EmployeeMasterSnapshot` | container rename only |

**Address decision (must implement in Phase 1):** The ContactDetails model
declares `address`/`present_address` (single line) while the write API uses
`address_line1/2`. To avoid loss, employee_master's `ContactDetails` will declare
**all of** `address, address_line1, address_line2` (and present_* equivalents).
Migration backfills `address_line1` from `address` when only `address` exists.
No data lost in either direction.

## C. Undeclared-but-persisted fields → declared in employee_master — Status KEEP

The 35 employment-type-specific fields (inventory §2.5) are currently stored
loose on the profile document. In employee_master they become **declared optional
fields** on `EmployeeMasterSnapshot` (grouped under an `engagement` sub-section in
docs but flat on the document for back-compat). This upgrades them from
"accidentally persisted" to "first-class", with zero data change.

Grouping (documentation only; storage stays flat):
- contract: contract_order_no, contract_start_date, contract_end_date,
  consolidated_pay, contract_authority, vendor_agency, renewal_allowed
- engagement: engagement_order_no, engagement_order_date, engagement_end_date,
  remuneration_type, muster_roll_number, daily_wage_rate, wage_rate_unit,
  engagement_office, nature_of_work, expected_duration_days, fixed_monthly_amount,
  basic_pay, pay_level, engagement_remarks
- deputation: deputation_order_no, parent_department, parent_designation,
  lien_status, deputation_start_date, deputation_end_date,
  deputation_allowance_percent
- outsourcing: outsourcing_order_no, agency_name, agency_contract_number,
  sla_reference, monthly_billing_rate, role_description
- attachments: document_ids

## D. Unknown / future-discovered fields → Status LEGACY

Any field found in the live `employee_profiles` / identity collections during
migration that is **not** in this inventory is written to
`legacy_fields: { <old_key>: <value> }` on the employee_master document, with a
log line `LEGACY_FIELD_PRESERVED <employee_id> <key>`. The migration report
counts these. They are never silently dropped.

## E. Ownership reassignments (FK, not data move)

These fields stay physically in employee_master but **reference** another context;
they are FKs, not owned master data:

| Field | References |
|---|---|
| current_department_id | organization_master.department |
| current_designation_id | organization_master.designation |
| current_office_id | organization_master.office |
| reporting_officer_id | employee_master.employee_id (self) |
| document_ids, photo_url, signature_url, thumb_impression_url | app_platform/documents |

## F. Cross-context join contract

`user.employee_id → employee_master.employee_id` (identity_access → employee_master).
A user account is **not** an employee record; the link is the only coupling.

## G. Acceptance check for Phase 9 migration report

For each row in `current_fields_inventory.md`, the report asserts one of:
`KEEP(present)`, `MAP(present at new name)`, `LEGACY(present in legacy_fields)`.
Target: **unmapped = 0, dropped = 0.**
