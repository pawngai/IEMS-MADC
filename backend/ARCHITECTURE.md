# MyIEMS Backend Architecture (Modular Monolith)

## Overview

The backend uses bounded contexts under `contexts/`, cross-cutting infrastructure in `app_platform/`, and shared primitives in `shared_kernel/`.

## Government 10/10 Strategic Split

Reference target ownership is enforced through `domain_separation/context_responsibilities.py` and collection ownership checks:

- `employee_identity`: Canonical employee identity (employee code, name, DOB, employment type)
- `employee_profile`: Profile enrichment and employee read projections
- `department`: Department-scoped portal orchestration over employee/profile/leave operations
- `service_book`: Canonical service-history bounded context for official records, read-side engine, and print surface (Parts I-VIII)
- `pay`: Financial ledger — owns `pay_ledger_entries` (pay revisions, allowance changes). Emits `PayRevised`/`AllowanceChanged` events via outbox. Service book Part VII consumes pay data indirectly via events/projections, not by direct write.
- `leave`: Leave ledger
- `ess`: Self-service portal
- `audit`: Immutable compliance log
- `reporting`: Read-only analytics — pure projection context with no owned collections. Runs aggregation pipelines against canonical context collections (`employee_identities`, `employee_profile_extensions`, `leave_applications`, `service_book_records`). Never writes.
- `seniority`: Seniority list management — owns `seniority_lists` (generated snapshots with rank overrides and DRAFT→PROVISIONAL→FINAL workflow). Reads canonical sources (`employee_identities`, `employee_profile_extensions`, `service_book_part_ii_a`) at generation time via cross-context queries in the application service layer.

## Boundary Rules

- `contexts/<X>/...` must not import `contexts/<Y>/...` for `X != Y`.
- `contexts/<X>/domain` must not import `contexts/<X>/infrastructure`.
- Shared primitives live in `shared_kernel/` and must remain small (`errors.py`, `ids.py`, `time.py`, `typing.py`).

These are enforced by `backend/tests/test_import_boundaries.py`.

## Contract Registry and Versioning

- Canonical contract registry lives in `app_platform/contracts/registry.py`.
- Events, commands, and queries are registered with explicit version keys (for example `EmployeeCreated.v1`).
- Outbox enqueue (`app_platform/outbox/repo.py`) validates payloads against registered schemas before write.
- Runtime service-event lifecycle emissions use the canonical `EventName.SERVICE_EVENT_*` names. Legacy custom names (`ServiceEventCreated`, `ServiceEventProposed`, `ServiceEventApproved`) have been retired from the registry; `test_legacy_compat_event_names_are_not_registered` keeps them from returning.

### Event Payload Ownership

Business event payload schemas are owned by their publishing bounded context:

- Employee identity events (`Employee*Event`): `contexts.employee_identity.contracts.events`
- Service-event lifecycle payloads (`ServiceEvent*Payload`): `contexts.service_book.records.contracts.events`
- Document lifecycle payloads (`Document*Payload`): `contexts.documents.contracts.events`
- Domain-neutral fallback (`LenientEventPayload`): `app_platform.contracts.events.core_events`

The platform layer hosts only the registration side-effect — schemas are
imported by `app_platform/contracts/events/__init__.py` for `register_event`
calls and never defined there. This is enforced by
`backend/tests/test_architecture_guardrails.py::test_app_platform_events_does_not_define_business_event_schemas`.

## Event Names

Defined in `app_platform/event_bus/types.py`:

- `LeaveApplied`
- `LeaveApproved`
- `LeaveRejected`

Event payloads are JSON-safe dictionaries and include actor/department metadata.

## Outbox Usage

Outbox files:

- `app_platform/outbox/model.py`
- `app_platform/outbox/repo.py`
- `app_platform/outbox/dispatcher.py`

Flow:

1. Use-case writes business change through current module gateway.
2. Use-case writes corresponding outbox event (`PENDING`).
3. Dispatcher polls pending events, publishes to in-process event bus.
4. Outbox row transitions to `SENT` or `FAILED` with retry metadata.

### Enforcement

- State-changing use-cases are guarded by `backend/tests/test_outbox_emitted_for_state_changes.py`.
- Direct event bus publishing from use-case files is blocked by `backend/tests/test_no_direct_eventbus_publish_in_usecases.py`.
- Request correlation (`X-Request-ID`) and optional `Idempotency-Key` are propagated into outbox metadata.

## Data Ownership Rules

- Ownership map is defined in `domain_separation/data_ownership.py`.
- Repository constructors for canonical read/write contexts assert collection ownership.
- Enforcement coverage for strategic collections is validated in `backend/tests/test_collection_ownership_enforced.py`.

## Service Book Context

- `contexts/service_book`: canonical Service Book bounded context for opening, parts, records, corrections, verification, projection, queries, and print/PDF surfaces.
- `contexts/service_book/records`: official append-only Service Book records, migrated from the former `service_events` context.
- Read-only API contract for service-book routes is enforced by `backend/tests/test_service_book_routes_are_read_only.py`.

## Service Book Records

- Records package: `contexts/service_book/records`.
- Aggregate lifecycle: `DRAFT -> PROPOSED -> APPROVED -> POSTED`.
- Approval emits `ServiceEventLifecycleApproved.v1` through outbox.
- Service-book reads consume projected collections only; ledger write APIs are retired.

## Department Context

- `contexts/department`: department-scoped portal API and orchestration for `/department/*` routes.
- Owns portal behavior such as dashboard, employee directory/snapshot, pending work, pending leaves, department-scoped employee actions, and the sanctioned-strength establishment aggregate.
- Department-owned sanctioned strength is persisted in `department_establishments` with append-only change logs in `department_establishment_logs`.
- Consumes employee/profile/leave behavior through contracts and approved adapters rather than owning employee truth.
- Department governance CRUD remains outside this context under `contexts/system_admin/department` and is mounted at `/departments/manage`.

## Identity / RBAC / Module Access

- `contexts/identity` owns login, refresh/logout, password flows, user sessions, and `/api/auth/module-access`.
- `contexts/rbac` owns authority and permission definitions.
- Authorities such as `GLOBAL_DATA_ENTRY` and `DEPT_DATA_ENTRY` are roles.
- Permissions such as `PROFILE_CREATE` and `SERVICE_BOOK_READ_ALL` are action grants.
- Module ids such as `data_entry`, `service_book`, `leave`, `audit`, `verification`, `approval`, and `attestation` are module visibility flags.
- Production module access infers safe baseline modules only when configuration is absent or unavailable.
- When `module_permissions.matrix` exists, it is authoritative and can disable an otherwise inferred module.
- Module access must not be treated as a backend write permission; owning contexts still enforce writes through authorities, permissions, and domain rules.

## Runtime Wiring

`app/bootstrap/container.py` creates app container with:

- `EventBus`
- `OutboxRepository`
- `OutboxDispatcher`

`app/bootstrap/subscribers.py` registers subscribers.
Dispatcher starts/stops with FastAPI startup/shutdown hooks in `app/main.py`.

### Current Subscribers

- `contexts.audit.application.subscribers`: writes audit entries for domain events.
- `contexts.employee_profile.contracts.subscribers`: maintains employee read-model projections.
- `contexts.notifications.application.subscribers`: writes employee notifications on `LeaveApproved`.
- `contexts.service_book.contracts.subscribers`: updates service book projections from events.
- `contexts.service_book.records.contracts.subscribers`: processes service event lifecycle transitions.

## Router Registration Split

API router composition is centralized in `app/bootstrap/router_registry.py`.

- `app/bootstrap/registrations/department.py` mounts the department portal router for `/department`.
- `app/bootstrap/registrations/employee_profile.py` mounts only `/employee-profiles` routes.
- `app/bootstrap/registrations/system_admin.py` mounts `/system-admin` plus department governance routes at `/departments/manage`.

This split is guarded by `backend/tests/test_bootstrap_registrations.py`.

## Namespace Policy

- Canonical infrastructure namespace is `app_platform.*`.
- Boundary tests fail if code reintroduces `platform.*` or other removed namespaces.
