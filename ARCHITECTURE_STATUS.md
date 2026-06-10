# Architecture Status

Generated: 2026-06-09

This inventory reflects the current source tree and runtime wiring.

## Backend Context Roots

| Context | Path | Ownership |
|---------|------|-----------|
| audit | `backend/contexts/audit/` | Immutable compliance logging |
| change_requests | `backend/contexts/change_requests/` | Workflow state and change management |
| department | `backend/contexts/department/` | Department portal orchestration and sanctioned-strength establishment aggregate |
| documents | `backend/contexts/documents/` | File storage, document metadata, and document lifecycle events |
| employee_identity | `backend/contexts/employee_identity/` | Canonical employee identity |
| employee_profile | `backend/contexts/employee_profile/` | Employee profile enrichment and read projections |
| ess | `backend/contexts/ess/` | Employee self-service portal |
| identity | `backend/contexts/identity/` | Authentication, sessions, and user management |
| leave | `backend/contexts/leave/` | Leave management ledger |
| notifications | `backend/contexts/notifications/` | Event-driven notifications |
| pay | `backend/contexts/pay/` | Pay and financial ledger records |
| rbac | `backend/contexts/rbac/` | Role, permission, and access-control domain |
| reporting | `backend/contexts/reporting/` | Read-only dashboards and analytics |
| seniority | `backend/contexts/seniority/` | Seniority list generation and workflow |
| service_book | `backend/contexts/service_book/` | Service Book opening, records, read-side projections, corrections, verification, and print/PDF surfaces |
| system_admin | `backend/contexts/system_admin/` | System administration and governance functions |
| workflow | `backend/contexts/workflow/` | Workflow engine and task state |

There is no standalone `backend/contexts/service_events` context. Current service-history mutation behavior lives under `backend/contexts/service_book/records`; legacy service-event terminology remains in event names, schemas, and compatibility-facing APIs.

## Backend Platform And Shared Roots

| Root | Path | Purpose |
|------|------|---------|
| app/bootstrap | `backend/app/bootstrap/` | App factory, dependency wiring, router composition, subscribers, seed/sync behavior |
| app_platform | `backend/app_platform/` | Cross-cutting platform services: auth, contracts, DB runtime, domain separation, event bus, forms, logging, outbox, reference data, settings, web helpers |
| shared_kernel | `backend/shared_kernel/` | Small primitives only: base errors/types, events, IDs, and generic types |

`backend/platform/` has been removed. New backend platform work belongs in `backend/app_platform/` or in the owning bounded context.

## Frontend Context Roots

| Context | Path |
|---------|------|
| access_control | `frontend/src/contexts/access_control/` |
| admin | `frontend/src/contexts/admin/` |
| analytics | `frontend/src/contexts/analytics/` |
| applications | `frontend/src/contexts/applications/` |
| audit | `frontend/src/contexts/audit/` |
| change_requests | `frontend/src/contexts/change_requests/` |
| department | `frontend/src/contexts/department/` |
| documents | `frontend/src/contexts/documents/` |
| employee_identity | `frontend/src/contexts/employee_identity/` |
| employee_profile | `frontend/src/contexts/employee_profile/` |
| ess | `frontend/src/contexts/ess/` |
| forms | `frontend/src/contexts/forms/` |
| identity | `frontend/src/contexts/identity/` |
| leave | `frontend/src/contexts/leave/` |
| masters | `frontend/src/contexts/masters/` |
| notifications | `frontend/src/contexts/notifications/` |
| pay | `frontend/src/contexts/pay/` |
| seniority | `frontend/src/contexts/seniority/` |
| service_book | `frontend/src/contexts/service_book/` |
| workflow | `frontend/src/contexts/workflow/` |

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

- EmployeeIdentity owns canonical employee identity.
- EmployeeProfile owns profile enrichment and employee read projections.
- Department owns department portal orchestration and Department-scoped sanctioned-strength establishment records.
- ServiceBook owns the current service-history runtime, including official records under `service_book/records`.
- Leave and Pay own their respective ledgers and emit events for downstream audit/projection behavior.
- Documents owns file storage, metadata, lifecycle events, and document boundary validation.
- Audit is append-only and receives events from contexts through subscribers.
- Reporting is read-only and performs aggregation against canonical collections.
- No cross-context DB writes are allowed.
- `shared_kernel` contains primitives only, never business logic.
- Identity owns authentication/session behavior and `/api/auth/module-access`.
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
| Employee identity lifecycle events | `contexts.employee_identity.contracts.events` |
| Service-event lifecycle payloads | `contexts.service_book.records.contracts.events` |
| Document lifecycle payloads | `contexts.documents.contracts.events` |
| Domain-neutral lenient payload | `app_platform.contracts.events.core_events` |

Event-name → schema registration happens in
`backend/app_platform/contracts/events/__init__.py` and is the only place the
platform layer references context-owned event types.

## Remaining Known Issues

1. Some historical reference docs may still use `service_events` as terminology for service-history lifecycle events. That should not be read as a standalone bounded context.
2. Compatibility route redirects (`/service-events/*` -> `/service-book/records`) remain in the runtime for older clients. Callers should prefer canonical Service Book Records routes. Legacy event-name strings (`ServiceEventCreated`, `ServiceEventProposed`, `ServiceEventApproved`) have been retired from the event contract registry.
