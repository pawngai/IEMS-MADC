# Architecture Status

Generated: 2026-06-11

This inventory reflects the current source tree and runtime wiring.

## Backend Context Roots

| Context | Path | Ownership |
|---------|------|-----------|
| audit | `backend/contexts/audit/` | Immutable compliance logging |
| change_requests | `backend/contexts/change_requests/` | Workflow state and change management |
| department | `backend/contexts/department/` | Department portal orchestration and sanctioned-strength establishment aggregate |
| documents | `backend/contexts/documents/` | File storage, document metadata, and document lifecycle events |
| employee_master | `backend/contexts/employee_master/` | Public boundary for current employee facts; canonical identity and profile implementations are relocated here as `identity/` and `profile/` subpackages |
| ess | `backend/contexts/ess/` | Employee self-service portal |
| identity_access | `backend/contexts/identity_access/` | Login, users, roles, permissions, sessions, and module access (merged former `identity` + `rbac`); exposes `identity/` and `rbac/` subpackages |
| leave | `backend/contexts/leave/` | Leave management ledger (current runtime) |
| leave_attendance | `backend/contexts/leave_attendance/` | Target consolidation context for leave applications, ledger, balances, and approval records. Scaffolded; not yet wired into the runtime router |
| notifications | `backend/contexts/notifications/` | Event-driven notifications |
| organization_master | `backend/contexts/organization_master/` | Departments, offices, designations, sanctioned strength, and establishment structures |
| pay | `backend/contexts/pay/` | Pay and financial ledger records (current runtime) |
| pay_benefits | `backend/contexts/pay_benefits/` | Target consolidation context for pay ledger, projections, benefits, and pay-related calculations. Scaffolded; not yet wired into the runtime router |
| reporting | `backend/contexts/reporting/` | Read-only dashboards and analytics (current runtime) |
| reporting_analytics | `backend/contexts/reporting_analytics/` | Target consolidation context for read-only projections and dashboards. Scaffolded; not yet wired into the runtime router |
| seniority | `backend/contexts/seniority/` | Seniority list generation and workflow |
| service_book | `backend/contexts/service_book/` | Service Book opening, records, read-side projections, corrections, verification, and print/PDF surfaces |
| system_admin | `backend/contexts/system_admin/` | System administration and governance functions |
| workflow | `backend/contexts/workflow/` | Workflow engine and task state |

The former `identity` and `rbac` contexts have been merged into `identity_access`, and the former `employee_identity` and `employee_profile` contexts have been relocated into `employee_master`; those standalone backend roots no longer exist.

`leave_attendance`, `pay_benefits`, and `reporting_analytics` are scaffolded target contexts for a later consolidation phase. They are not registered in `backend/app/bootstrap/router_registry.py`; the `leave`, `pay`, and `reporting` contexts remain the live runtime.

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
| analytics | `frontend/src/contexts/analytics/` | |
| applications | `frontend/src/contexts/applications/` | |
| audit | `frontend/src/contexts/audit/` | |
| change_requests | `frontend/src/contexts/change_requests/` | |
| department | `frontend/src/contexts/department/` | |
| documents | `frontend/src/contexts/documents/` | |
| employee_identity | `frontend/src/contexts/employee_identity/` | Legacy source of truth; pending migration into `employee_master` |
| employee_master | `frontend/src/contexts/employee_master/` | Facade only; implementation still lives in `employee_identity`/`employee_profile` |
| employee_profile | `frontend/src/contexts/employee_profile/` | Legacy source of truth; pending migration into `employee_master` |
| ess | `frontend/src/contexts/ess/` | |
| forms | `frontend/src/contexts/forms/` | |
| identity | `frontend/src/contexts/identity/` | Legacy source of truth; pending migration into `identity_access` |
| identity_access | `frontend/src/contexts/identity_access/` | Facade (`export * from "@/contexts/identity"`) plus permission/portal selectors |
| leave | `frontend/src/contexts/leave/` | |
| leave_attendance | `frontend/src/contexts/leave_attendance/` | Scaffold/stub for later consolidation |
| masters | `frontend/src/contexts/masters/` | |
| notifications | `frontend/src/contexts/notifications/` | |
| organization_master | `frontend/src/contexts/organization_master/` | Scaffold/stub for later consolidation |
| pay | `frontend/src/contexts/pay/` | |
| pay_benefits | `frontend/src/contexts/pay_benefits/` | Scaffold/stub for later consolidation |
| reporting_analytics | `frontend/src/contexts/reporting_analytics/` | |
| seniority | `frontend/src/contexts/seniority/` | |
| service_book | `frontend/src/contexts/service_book/` | |
| workflow | `frontend/src/contexts/workflow/` | |

The frontend identity/employee consolidation trails the backend. `identity_access` and `employee_master` exist as thin facades, but the real implementations remain in the legacy `identity`, `employee_identity`, and `employee_profile` contexts, which are still the active import targets. Retiring those legacy contexts is a pending phase.

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
- Department owns department portal orchestration and Department-scoped sanctioned-strength establishment records.
- ServiceBook owns the current service-history runtime, including official records under `service_book/records`.
- Leave and Pay own their respective ledgers and emit events for downstream audit/projection behavior.
- Documents owns file storage, metadata, lifecycle events, and document boundary validation.
- Audit is append-only and receives events from contexts through subscribers.
- Reporting is read-only and performs aggregation against canonical collections.
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
2. The identity/employee consolidation is partially complete and asymmetric across layers. The backend has fully merged `identity`/`rbac` into `identity_access` and relocated `employee_identity`/`employee_profile` into `employee_master`, removing the legacy roots. The frontend still ships those legacy contexts as the active source of truth, with `identity_access`/`employee_master` present only as facades. Retiring the legacy frontend contexts is a pending phase.
3. The backend `leave_attendance`, `pay_benefits`, and `reporting_analytics` contexts are scaffolds for a later consolidation phase and are not wired into the runtime router. The `leave`, `pay`, and `reporting` contexts remain live.
4. Compatibility route redirects (`/service-events/*` -> `/service-book/records`) remain in the runtime for older clients. Callers should prefer canonical Service Book Records routes. Legacy event-name strings (`ServiceEventCreated`, `ServiceEventProposed`, `ServiceEventApproved`) have been retired from the event contract registry.
