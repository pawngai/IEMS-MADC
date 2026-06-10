# Service Book vs Onboarding/Profile Coverage Matrix

## Scope
This matrix compares **Service Book Part I / II / III** model fields against what is currently captured by:
- Employee onboarding/profile schema and profile workflow mapping
- Dynamic form configuration

## Current Verdict
- **Part I:** Partial coverage
- **Part II-A:** Mismatch between model and form (semantic mismatch)
- **Part II-B:** Not represented in onboarding/profile workflow
- **Part III:** Not represented in onboarding/profile workflow

## Current Runtime Notes

- Only regular employees are eligible for Service Book.
- Service Book Records own the current service-history mutation runtime.
- `service_book` module access controls frontend/module visibility and route access, but it does not override regular-employee eligibility or backend Service Book permissions.
- Employee onboarding/profile creation remains split between regular and non-regular create flows in the global Employee Directory.

---

## Part I (Bio-Data)

### Covered today (via profile + Part I auto-map)
- `name_in_block_letters` (mapped from `full_name`)
- `parent_name`, `father_name`, `mother_name`
- `nationality`, `caste_category`
- `date_of_birth_christian`
- `photograph_url`
- `phone_number`, `email`
- `permanent_address` (from contact address fields)
- `attesting_officer_*` + `attestation_date` (during attestation flow)

### Missing / not reliably captured from onboarding/profile
- Identity extras: `sub_caste`, `religion` (religion exists in profile but not mapped in current Part I mapper)
- DOB alternate: `date_of_birth_saka`, `place_of_birth`
- Qualifications arrays:
  - `educational_qualifications_initial`
  - `educational_qualifications_acquired`
  - `professional_qualifications`
- Physical details: `height_cm`, `identification_marks`, `blood_group` (blood group exists in profile but not mapped)
- Additional address/contact fields:
  - `present_address`
  - richer `emergency_contact` structure
- Signatures: `signature_url`, `thumb_impression_url`

---

## Part II-A

### Model expectation (parts_model)
Part II-A is certificate/attestation-oriented:
- Medical: `medical_fitness_certificate`, `medical_exam_date`, `medical_officer_name`, `medical_category`
- Character/police verification fields
- Oaths/declarations
- Initial property return
- Confirmation fields

### Dynamic form currently configured
`service_book_part_ii_a` is configured as **service event** fields:
- `event_type_code`, `order_number`, `order_date`, `effective_date`
- `designation_code`, `department_code`, `office_name`
- `pay_level_code`, `basic_pay`

### Gap
- **Semantic mismatch:** Form fields do not match Part II-A model fields.
- This is not just missing fields; it is a domain/model contract mismatch.

---

## Part II-B (Mutable Certificates)

### Model expectation
- `family_members`
- `gpf_account_number` (PCF account number), `gpf_nomination` (PCF nomination)
- DCR gratuity / family pension nomination fields
- NPS nomination and bank details
- Leave encashment nomination
- NPS PRAN/nomination
- Bank details

### Workflow coverage today
- Some nominee fields exist in profile schema (`gpf_*` for PCF, `gratuity_*`, `insurance_*`)
- But there is **no dedicated Part II-B dynamic form/config path** and no full Part II-B lifecycle in onboarding/profile workflow.

### Gap
- No complete II-B workflow representation.
- No comprehensive mapping from profile nominee subset to full II-B structure.

---

## Part III (Service History Outside Current Appointment)

### Model expectation
- `previous_services` (with qualifying service details)
- `total_previous_qualifying_service`
- `foreign_services`
- verification metadata (`verified`, `verified_by`, `verification_date`)

### Workflow coverage today
- Not present in onboarding/profile schema.
- No Part III dynamic form entry found.

### Gap
- Entire Part III domain is absent from onboarding/profile workflow.

---

## Recommended Implementation Order

1. **Align Part II-A contract first**
   - Decide whether Part II-A should be certificates (current model) or service events (current form).
   - Update either model or dynamic form so both represent the same domain.

2. **Expand Part I mapper + profile input set**
   - Add missing fields where appropriate to onboarding/profile inputs.
   - Extend `build_part_i_from_profile` mapping for already-available fields.

3. **Introduce dedicated Part II-B workflow/form**
   - Add dynamic form config and persistence path for full II-B structure.

4. **Introduce dedicated Part III workflow/form**
   - Add previous service + foreign service capture and verification metadata flow.

5. **Add automated coverage tests**
   - Add tests that assert required Service Book fields are captured (or explicitly N/A) at each onboarding stage.

---

## Practical Acceptance Criteria

- For each Part (I, II-A, II-B, III), define required fields and source of truth.
- Profile/onboarding payload + dynamic forms can populate all required fields (or explicit defaults).
- No model/form semantic mismatch remains.
- Regression tests fail if required field coverage drops.
