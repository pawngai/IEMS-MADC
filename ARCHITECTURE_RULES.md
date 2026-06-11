# ARCHITECTURE_RULES

Date: 2026-06-09
Status: Current implementation

## Core Truth Rules

1. Universal employee truth
- Every employee has an EmployeeIdentity record and an EmployeeProfile record.
- EmployeeIdentity is the canonical source for employee identity and master attributes (employee code, name, DOB, employment type).
- EmployeeProfile owns profile enrichment and read projections built on top of identity data.
- Other contexts must consume employee truth via contracts/services only.

2. Regular-only Service Book
- Service Book applies only to `employment_type == REGULAR`.
- Eligibility must be enforced before create/read/update/print operations.
- Non-regular employees must not receive service-book ledger/projection entries.

3. Service history ownership
- Service Book is the official service-history record for eligible employees.
- Service Book Records under `backend/contexts/service_book/records` own current service-history mutation behavior.
- Legacy service-event names remain in event contracts and compatibility-facing APIs, but there is no standalone `service_events` bounded context.
- Workflow stores process-state metadata only; it must not store domain truth payloads.

4. Documents ownership
- Documents context owns file storage and metadata linking.
- Documents metadata cannot define service-history truth.

5. Department ownership split
- Department context owns department-scoped portal orchestration and `/department/*` routing.
- Department context owns the sanctioned-strength establishment aggregate and its Department-scoped write model.
- EmployeeProfile remains the owner of employee profile enrichment and projections used by department flows.
- SystemAdmin owns department governance CRUD at `/departments/manage/*` and must not write sanctioned strength.

## Access-Control Model

Scopes are mandatory in both backend authorization and frontend capability routing:

- `GLOBAL`: cross-department
- `DEPARTMENT`: restricted to actor department
- `EMPLOYEE`: self scope only

Authorization logic must use canonical access-control services:

- Backend: `contexts.rbac.application.access_control` and `contexts.rbac.application.authorization_service`
- Frontend: `contexts/access_control/services/authorizationService.js`

Authorities, permissions, and module visibility must stay separate:

- Authorities/roles include values such as `GLOBAL_DATA_ENTRY`, `DEPT_DATA_ENTRY`, `VERIFIER`, and `SYSTEM_ADMIN`.
- Permissions include action grants such as `PROFILE_CREATE`, `PROFILE_READ_ALL`, and `SERVICE_BOOK_READ_ALL`.
- Module ids include visibility flags such as `data_entry`, `service_book`, `leave`, `audit`, `verification`, `approval`, and `attestation`.
- `/api/auth/module-access` may hide/show modules and route surfaces, but backend writes must still be enforced by owning-context authority, permission, and domain rules.
- Missing production module config may infer a safe baseline from authorities/permissions; configured `module_permissions.matrix` is authoritative when present.

## Context Topology

Backend target structure:

- `backend/contexts/employee_identity/{domain,application,contracts,services,repository,api,schemas}`
- `backend/contexts/employee_profile/{domain,services,repository,api,schemas,read_model}`
- `backend/contexts/organization_master/{domain,services,repository,api}`
- `backend/contexts/service_book/{domain,application,repository,api,schemas,mappers,read_side,records,opening,parts,projection,queries,verification,corrections,pdf}`
- `backend/contexts/leave_attendance/{domain,services,repository,api,schemas}`
- `backend/contexts/pay_benefits/{domain,services,repository,api}`
- `backend/contexts/documents/{domain,application,infrastructure,services,repository,api}`
- `backend/contexts/audit/{domain,services,repository,api}`
- `backend/contexts/seniority/{domain,application,api}`
- `backend/app_platform/{auth,config,contracts,db,domain_separation,event_bus,forms,form_schema,logging,outbox,policy_engine,reference_data,web}`
- `backend/shared_kernel/{events,base,ids,types}`
- `backend/server.py`

Frontend target structure:

- `frontend/src/app`
- `frontend/src/contexts/{department,employee_identity,employee_profile,service_book,leave,pay,documents,audit,...}`
- `frontend/src/shared/{ui,lib,api,types}`
- `frontend/src/features`
- `frontend/src/platform/{api,auth,errors,permissions}`
- `frontend/src/portals`

## Import and Boundary Constraints

1. No cross-context infrastructure internals
- Context A must not import Context B `infrastructure.repo*` / `infrastructure.repository*` internals.

2. Cross-context access via contracts/services
- Allowed patterns: explicit contracts, service facades, and approved boundary adapters.

3. Shared stays generic
- `shared` and `shared_kernel` must not own domain-specific business truth.

4. Workflow and documents boundary
- Workflow payloads must remain process-state metadata.
- Documents metadata must reject service-history truth keys.

## Canonical Service Contracts

Identity domain services (owned by `employee_identity`):

- `determineEmploymentType`
- `isServiceBookEligible`
- `updateEmployeeStatus`

These contracts are the single source for employment-type normalization and service-book eligibility semantics.
The canonical definitions live in `contexts.employee_identity.domain.identity_normalization` and are
published via `contexts.employee_identity.contracts.employee_domain`. The previous
`employee_profile.domain.profile_normalization` mirror has been retired
(enforced by `test_employee_profile_profile_normalization_mirror_stays_deleted`).

## Event Ownership

Business event payload schemas are owned by their publishing bounded context and
must NOT be defined in `app_platform`. The platform hosts only the event bus
mechanism, the registry, and the domain-neutral `LenientEventPayload` primitive.

| Event family | Owning context | Module |
|--------------|----------------|--------|
| Employee identity lifecycle (Created, IdentityCreated, Updated, StatusChanged, Promoted) | `employee_identity` | `contexts.employee_identity.contracts.events` |
| Service-event lifecycle (Approved, Recorded, Corrected, Voided, Lifecycle, DocumentAttached) | `service_book` (records) | `contexts.service_book.records.contracts.events` |
| Document lifecycle (Uploaded, Locked, MetadataUpdated, Deleted) | `documents` | `contexts.documents.contracts.events` |

Registration of every event name → schema happens in
`backend/app_platform/contracts/events/__init__.py`, which imports the
context-owned schemas. This is the only place the platform touches business
event types, and it does so only for the registration side-effect.

Enforcement: `test_app_platform_events_does_not_define_business_event_schemas`,
`test_employee_event_schemas_live_in_employee_identity_context`,
`test_app_platform_employee_events_module_stays_deleted`.

## Policy Engine Ownership

`app_platform.policy_engine` hosts ONLY the technical `Decision` value object.
Business-domain facts and rules are owned by the context they describe:

| Policy | Owning context | Module |
|--------|----------------|--------|
| Leave-request approval (CCS leave rules, maternity/paternity/CCL eligibility, balance/spell checks) | `leave` | `contexts.leave_attendance.domain.leave_request_policy`, `contexts.leave_attendance.application.evaluate_leave_request` |
| Change-request gating | `change_requests` | `contexts.change_requests.domain.change_request_policy`, `contexts.change_requests.application.evaluate_change_request` |

Enforcement: `test_policy_engine_is_platform_primitive_only`,
`test_leave_request_policy_lives_in_leave_context`,
`test_change_request_policy_lives_in_change_requests_context`.

## Domain Layer Cross-Context Boundary

A context's domain layer must never import another context's modules — not
even another context's `contracts`. Cross-context coupling belongs in the
**application layer** (orchestration) or the **contracts layer** (anti-
corruption). The RBAC enums in `contexts.rbac.domain.models` and
`contexts.rbac.application.access_control` are the only platform-wide
exception. Enforcement: `test_domain_layer_has_no_cross_context_imports`.
