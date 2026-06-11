# Architecture Status

Generated: 2026-06-12

This inventory reflects the current source tree and runtime wiring.

## Backend Context Roots

| Context | Path | Ownership |
|---------|------|-----------|
| audit | `backend/contexts/audit/` | Immutable compliance logging |
| change_requests | `backend/contexts/change_requests/` | Workflow state and change management |
| documents | `backend/contexts/documents/` | File storage, document metadata, and document lifecycle events |
| employee_master | `backend/contexts/employee_master/` | Public boundary for current employee facts; canonical identity and profile implementations are relocated here as `identity/` and `profile/` subpackages |
| ess | `backend/contexts/ess/` | Employee self-service portal |
| identity_access | `backend/contexts/identity_access/` | Login, users, roles, permissions, sessions, and module access (merged former `identity` + `rbac`); exposes `identity/` and `rbac/` subpackages |
| leave_attendance | `backend/contexts/leave_attendance/` | Leave applications, ledger, balances, and approval records (current runtime) |
| notifications | `backend/contexts/notifications/` | Event-driven notifications |
| organization_master | `backend/contexts/organization_master/` | Departments, offices, designations, sanctioned strength, establishment structures, and the department portal orchestration (current runtime) |
| pay_benefits | `backend/contexts/pay_benefits/` | Pay ledger, projections, benefits, and pay-related calculations (current runtime) |
| reporting_analytics | `backend/contexts/reporting_analytics/` | Read-only projections and dashboards (current runtime) |
| seniority | `backend/contexts/seniority/` | Seniority list generation and workflow |
| service_book | `backend/contexts/service_book/` | Service Book opening, records, read-side projections, corrections, verification, and print/PDF surfaces |
| system_admin | `backend/contexts/system_admin/` | System administration and governance functions |
| workflow | `backend/contexts/workflow/` | Workflow engine and task state |

The former `identity` and `rbac` contexts have been merged into `identity_access`, and the former `employee_identity` and `employee_profile` contexts have been relocated into `employee_master`; those standalone backend roots no longer exist.

The context consolidation is complete: the former `leave`, `pay`, `reporting`, and `department` contexts have been absorbed into `leave_attendance`, `pay_benefits`, `reporting_analytics`, and `organization_master`, which are the live runtime contexts registered through `backend/app/bootstrap/registrations/`. The legacy roots no longer exist.

There is no standalone `backend/contexts/service_events` context. Current service-history mutation behavior lives under `backend/contexts/service_book/records`; legacy service-event terminology remains in event names, schemas, and compatibility-facing APIs.

## Backend Platform And Shared Roots

| Root | Path | Purpose |
|------|------|---------|
| app/bootstrap | `backend/app/bootstrap/` | App factory, dependency wiring, router composition, subscribers, seed/sync behavior |
| app_platform | `backend/app_platform/` | Cross-cutting platform services: auth, contracts, DB runtime, domain separation, event bus, forms, logging, outbox, reference data, settings, web helpers |
| shared_kernel | `backend/shared_kernel/` | Small primitives only: base errors/types, events, IDs, and generic types |

`backend/platform/` has been removed. New backend platform work belongs in `backend/app_platform/` or in the owning bounded context.

## Frontend Context Roots

| Context | Path | Migration state |
|---------|------|-----------------|
| access_control | `frontend/src/contexts/access_control/` | |
| admin | `frontend/src/contexts/admin/` | |
| applications | `frontend/src/contexts/applications/` | |
| audit | `frontend/src/contexts/audit/` | |
| change_requests | `frontend/src/contexts/change_requests/` | |
| documents | `frontend/src/contexts/documents/` | |
| employee_master | `frontend/src/contexts/employee_master/` | Owns employee identity + profile UI/api/model (legacy `employee_identity`/`employee_profile` contexts retired) |
| ess | `frontend/src/contexts/ess/` | |
| forms | `frontend/src/contexts/forms/` | |
| identity_access | `frontend/src/contexts/identity_access/` | Owns auth/session, RBAC, and permission/portal selectors (legacy `identity` context retired) |
| leave_attendance | `frontend/src/contexts/leave_attendance/` | Owns leave UI/api/model (legacy `leave` context retired) |
| notifications | `frontend/src/contexts/notifications/` | |
| organization_master | `frontend/src/contexts/organization_master/` | Owns department portal and masters UI/api/model (legacy `department` + `masters` contexts retired) |
| pay_benefits | `frontend/src/contexts/pay_benefits/` | Owns pay domain services (legacy `pay` context retired) |
| reporting_analytics | `frontend/src/contexts/reporting_analytics/` | Owns analytics dashboards (legacy `analytics` context retired) |
| seniority | `frontend/src/contexts/seniority/` | |
| service_book | `frontend/src/contexts/service_book/` | |
| workflow | `frontend/src/contexts/workflow/` | |

The frontend consolidations are complete and mirror the backend. The legacy `identity`, `employee_identity`, `employee_profile`, `leave`, `pay`, `analytics`, `department`, and `masters` contexts have been retired; their implementations were relocated into `identity_access`, `employee_master`, `leave_attendance`, `pay_benefits`, `reporting_analytics`, and `organization_master`, which are the sole import targets.

There is no standalone `frontend/src/contexts/service_events` context. Service record UI lives under `frontend/src/contexts/service_book/records`.

## Frontend Shell And Platform Roots

| Root | Path | Purpose |
|------|------|---------|
| app | `frontend/src/app/` | Layouts, pages, providers, and router composition |
| contexts | `frontend/src/contexts/` | Domain-owned UI, model, API, and service code |
| features | `frontend/src/features/` | Thin feature entrypoints retained by target topology |
| platform | `frontend/src/platform/` | Domain-neutral API, auth, error, and permission helpers |
| portals | `frontend/src/portals/` | Portal entrypoint contracts |
| shared | `frontend/src/shared/` | Context-agnostic UI, utilities, API/types primitives |

Frontend route composition is in `frontend/src/app/router`, and provider composition is in `frontend/src/app/providers`.

## Target Ownership Model

- EmployeeMaster owns the public boundary for current employee facts, including the canonical identity and profile implementations relocated into its `identity/` and `profile/` subpackages.
- OrganizationMaster owns department portal orchestration, masters/reference structures, and Department-scoped sanctioned-strength establishment records.
- ServiceBook owns the current service-history runtime, including official records under `service_book/records`.
- LeaveAttendance and PayBenefits own their respective ledgers and emit events for downstream audit/projection behavior.
- Documents owns file storage, metadata, lifecycle events, and document boundary validation.
- Audit is append-only and receives events from contexts through subscribers.
- ReportingAnalytics is read-only and performs aggregation against canonical collections.
- No cross-context DB writes are allowed.
- `shared_kernel` contains primitives only, never business logic.
- IdentityAccess owns authentication/session behavior, roles/permissions, and `/api/auth/module-access` (merged former Identity + RBAC).
- Module access flags are module visibility ids, not roles or permissions. Missing production module config infers a safe baseline; configured `module_permissions.matrix` is authoritative when present.

## Architecture Guardrails In Place

### Backend Tests

| Test File | What It Enforces |
|-----------|------------------|
| `backend/tests/test_import_boundaries.py` | Cross-context import allowlist, domain-to-infrastructure restrictions, stale allowlist detection, removed namespace guards |
| `backend/tests/test_context_boundaries.py` | Cross-context infrastructure import restrictions |
| `backend/tests/test_context_isolation_whole_repo.py` | Whole-repo infrastructure isolation |
| `backend/tests/test_target_architecture_enforcement.py` | Current backend topology, removed service-events context, app platform roots, shared-kernel roots |
| `backend/tests/test_cross_context_collection_isolation.py` | MongoDB collection ownership boundaries |
| `backend/tests/test_collection_ownership_enforced.py` | Repository collection ownership checks |
| `backend/tests/test_frontend_feature_architecture.py` | Frontend top-level topology and context import boundaries |

### Frontend Lint And Tests

| Check | What It Enforces |
|-------|------------------|
| `frontend/eslint.config.js` | Restricted imports across shared, platform, app, portal, and context layers |
| `frontend/src/contexts/__tests__/contextBoundary.test.js` | Context-to-context allowlist and shared/UI restrictions |
| `frontend/src/app/router/__tests__/routesImportGuard.test.js` | Router import boundaries and removed page namespace protection |

## Event Payload Ownership

Business event payload schemas are owned by their publishing context. The platform
hosts only the event registry and the domain-neutral `LenientEventPayload`.

| Event family | Owning module |
|--------------|---------------|
| Employee identity lifecycle events | `contexts.employee_master.contracts.events` |
| Service-event lifecycle payloads | `contexts.service_book.records.contracts.events` |
| Document lifecycle payloads | `contexts.documents.contracts.events` |
| Domain-neutral lenient payload | `app_platform.contracts.events.core_events` |

Event-name → schema registration happens in
`backend/app_platform/contracts/events/__init__.py` and is the only place the
platform layer references context-owned event types.

## Remaining Known Issues

1. Some historical reference docs may still use `service_events` as terminology for service-history lifecycle events. That should not be read as a standalone bounded context.
2. The identity and employee consolidations are complete on both layers: `identity`/`rbac` are merged into `identity_access`, and `employee_identity`/`employee_profile` are relocated into `employee_master`, with the legacy roots removed on both backend and frontend.
3. The backend and frontend context consolidations are complete: `leave_attendance`, `pay_benefits`, `reporting_analytics`, and `organization_master` own their implementations directly, and the legacy `leave`, `pay`, `reporting`, `department`, `analytics`, and `masters` roots have been removed on both layers.
4. Compatibility route redirects (`/service-events/*` -> `/service-book/records`) remain in the runtime for older clients. Callers should prefer canonical Service Book Records routes. Legacy event-name strings (`ServiceEventCreated`, `ServiceEventProposed`, `ServiceEventApproved`) have been retired from the event contract registry.
