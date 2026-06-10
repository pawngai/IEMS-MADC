# ARCHITECTURE_TESTS

Date: 2026-06-09
Status: Current implementation

This document lists the active architecture and boundary enforcement suites.

## Primary Guardrail Suite

File: `backend/tests/test_architecture_guardrails.py`

1. `test_service_book_creation_rejects_non_regular_employee`
- Protects regular-only Service Book eligibility.

2. `test_contexts_do_not_import_other_context_repository_internals`
- Blocks cross-context repository-internal imports.

3. `test_workflow_rejects_service_history_truth_payloads`
- Prevents workflow payloads from becoming business-truth storage.

4. `test_documents_context_cannot_store_service_history_truth`
- Enforces documents metadata boundary.

5. `test_role_checks_do_not_bypass_access_control`
- Prevents direct authority parsing/deprecated auth helper usage.

6. `test_app_platform_events_does_not_define_business_event_schemas`
- Blocks business event payload classes (Employee*, ServiceEvent*, Document*) from being defined under `app_platform/contracts/events/`.

7. `test_employee_event_schemas_live_in_employee_identity_context`
- Requires the canonical Employee*Event schemas to live in `contexts.employee_identity.contracts.events`.

8. `test_service_event_approved_payload_lives_in_service_book_records`
- Requires `ServiceEventApprovedPayload` to live in `contexts.service_book.records.contracts.events`.

9. `test_app_platform_employee_events_module_stays_deleted`
- Prevents the legacy `app_platform/contracts/events/employee_events.py` business-event module from being recreated.

10. `test_employee_profile_profile_normalization_mirror_stays_deleted`
- Prevents the retired `employee_profile.domain.profile_normalization` mirror (and its `contracts/employee_domain.py` re-export shim) from returning.

11. `test_policy_engine_is_platform_primitive_only`
- Restricts `app_platform/policy_engine/` to `__init__.py` + `decision.py` only — no business-domain facts or rules.

12. `test_leave_request_policy_lives_in_leave_context`
- Requires `LeaveFacts` and `LEAVE_RULES` to live in `contexts.leave.domain.leave_request_policy`.

13. `test_change_request_policy_lives_in_change_requests_context`
- Requires `ChangeRequestFacts` to live in `contexts.change_requests.domain.change_request_policy`.

14. `test_legacy_compat_event_names_are_not_registered` (in `test_contract_registry_complete.py`)
- Blocks `ServiceEventCreated`, `ServiceEventProposed`, `ServiceEventApproved` from being re-registered.

15. `test_domain_layer_has_no_cross_context_imports` (in `test_import_boundaries.py`)
- Blocks any `contexts/<X>/domain/` module from importing `contexts.<Y>.*` (other than the universally-allowed RBAC enums).

## Additional Architecture/Boundary Suites

1. `backend/tests/test_import_boundaries.py`
- Validates allowed cross-context import prefixes and denies unauthorized context coupling.
- `test_cross_context_allowlist_has_no_stale_entries`: ensures the allowlist stays honest by failing on prefixes that are no longer imported.

2. `backend/tests/test_context_boundaries.py`
- Blocks cross-context `infrastructure` imports.

3. `backend/tests/test_context_isolation_whole_repo.py`
- Enforces repo-wide infrastructure isolation from a whole-repo perspective.

4. `backend/tests/test_cross_context_collection_isolation.py`
- Enforces MongoDB collection ownership boundaries across bounded contexts.
- `test_no_cross_context_collection_access`: blocks any context from reading collections owned by another context (unless transitionally allowlisted).
- `test_no_cross_context_collection_writes`: stricter check that blocks INSERT/UPDATE/DELETE on foreign collections.
- Transitional allowlist tracks known violations with TODO comments for elimination.

5. `backend/tests/test_target_architecture_enforcement.py`
- Enforces backend target topology for contexts, app-platform, shared-kernel, removed `service_events` context, and Service Book Records required files.
- Supports two modes via `ARCH_ENFORCEMENT_MODE`:
	- `final` (default): requires exact final architecture with no transition namespaces.
	- `staged`: reserved for explicitly-listed transition namespaces when a migration needs it.

6. `backend/tests/test_bootstrap_registrations.py`
- Verifies router ownership split at bootstrap composition time.
- Confirms `/department` is mounted from the department registration module.
- Confirms `/employee-profiles` remains under employee_profile registration.
- Confirms `/departments/manage` remains under system_admin registration.

7. `backend/tests/test_identity_service_contract.py`
- Verifies auth/session contract behavior, including `/api/auth/module-access`.
- Ensures production fallback can infer role-appropriate baseline modules when config is absent.
- Ensures configured `module_permissions.matrix` is authoritative and can disable inferred module access.

8. `backend/tests/test_collection_ownership_enforced.py`
- Verifies repository constructors reject foreign collections.
- Includes Department-owned `department_establishments` and `department_establishment_logs` in the enforced ownership map.

9. `backend/tests/test_frontend_feature_architecture.py`
- Enforces frontend target topology: `src/{app,contexts,features,platform,portals,shared}` with required context and shared subdirectories.
- Supports two modes via `FRONTEND_ARCH_ENFORCEMENT_MODE`:
	- `final` (default): requires exact target top-level frontend directories and disallows legacy core-domain feature imports.
	- `staged`: reserved for explicitly-listed transition folders when a migration needs it.

10. `backend/tests/test_reference_architecture_context_split.py`
- Validates registered target context responsibilities.

## Runtime Contract Suites Added During Refactor

1. `backend/tests/test_service_book_regular_eligibility.py`
- Verifies service-book eligibility gate behavior.

2. `backend/tests/test_service_event_domain_service.py`
- Verifies service-event classification/payload/route semantics.

3. `backend/tests/test_workflow_domain_service.py`
- Verifies workflow transition action constraints.

4. `backend/tests/test_operational_context_services.py`
- Verifies leave/pay/documents service delegation and boundaries.

5. `backend/tests/test_ess_audit_domain_services.py`
- Verifies ESS self-scope guard and audit-trail route behavior.

6. `backend/tests/test_department_portal_service.py`
- Verifies Department portal orchestration, including Department-owned sanctioned-strength read/write behavior.

7. `backend/tests/test_department_establishment_backfill.py`
- Verifies sanctioned-strength backfill into `department_establishments` and safe cleanup of legacy `departments.metadata.sanctioned_strength`.

## Frontend Boundary Suites

1. `frontend/src/contexts/__tests__/contextBoundary.test.js`
- Verifies context-to-context import allowlists remain explicit and current.
- Fails on stale allowlist entries after architecture cleanup.

2. `frontend/src/app/router/__tests__/employeeEditorRouteConfig.test.js`
- Verifies employee and department editor route composition.
- Guards department portal wrappers and gateway usage from regressing to direct employee-profile imports.

3. `frontend/src/contexts/employee_identity/pages/__tests__/EmployeeDirectoryPage.serviceEvents.test.jsx`
- Verifies global Employee Directory behavior, including regular/non-regular create actions for `GLOBAL_DATA_ENTRY`/`DEALING_ASSISTANT` users with `PROFILE_CREATE`.
- Guards the create actions from depending on the `data_entry` module visibility flag.

## Run Commands

```powershell
c:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest backend/tests/test_architecture_guardrails.py -q
c:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest backend/tests/test_import_boundaries.py backend/tests/test_context_boundaries.py backend/tests/test_context_isolation_whole_repo.py backend/tests/test_target_architecture_enforcement.py -q
$env:ARCH_ENFORCEMENT_MODE='final'; c:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest backend/tests/test_target_architecture_enforcement.py -q
$env:FRONTEND_ARCH_ENFORCEMENT_MODE='final'; c:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest backend/tests/test_frontend_feature_architecture.py -q
c:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest backend/tests -q
```

CI requirement: architecture and boundary suites must run for any backend change touching `contexts/**`, `rbac_policy/**`, or cross-context contracts.
