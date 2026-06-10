# MyIEMS App Code Documentation

This document explains how the current codebase is organized and where major behavior lives.
It is intended for contributors who need to navigate, extend, or troubleshoot the app safely.

Focused implementation notes:

- Document management: `docs/reference/document-management-implementation.md`

## 1. High-Level System Shape

MyIEMS is a modular monolith with bounded contexts.

- Backend: FastAPI + MongoDB, context-owned domain/application/infrastructure code under `backend/contexts`.
- Frontend: React + Vite, context-owned UI/model/api code under `frontend/src/contexts`.
- App shell and platform layers provide cross-cutting infrastructure (routing, auth, forms, event bus, outbox, policy engine).

Core architecture constraints:

- Use bounded contexts only.
- EmployeeIdentity owns canonical employee identity.
- EmployeeProfile owns employee profile enrichment and projections.
- ServiceBook owns the current service-history runtime, including official records under `service_book/records`.
- Older `service_events` terminology survives in event names and compatibility contracts, but there is no standalone `backend/contexts/service_events` runtime context.
- No cross-context DB writes.
- `shared_kernel` contains primitives only (no business logic).

## 2. Backend Code Map

### 2.1 Backend entrypoints

- Canonical app: `backend/app/main.py` -> `create_app()` from app factory.
- App factory: `backend/app/bootstrap/app_factory.py`.
- Legacy compatibility entrypoint: `backend/server.py` (imports app from `app.main`).

Startup lifecycle in `app_factory.py`:

1. DB lifespan bootstraps DB runtime.
2. Container wiring (`wire_app_container`) creates EventBus and Outbox components.
3. Subscriber registration attaches context subscribers to EventBus.
4. Outbox dispatcher starts and stops with app lifecycle.
5. API router mounted at `/api`.

### 2.2 API registration flow

Router assembly is centralized in:

- `backend/app/bootstrap/router_registry.py`

Registration modules:

- `backend/app/bootstrap/registrations/core.py` -> auth + masters.
- `backend/app/bootstrap/registrations/employee_identity.py` -> employee identity.
- `backend/app/bootstrap/registrations/employee_profile.py` -> employee profile.
- `backend/app/bootstrap/registrations/department.py` -> department portal routes.
- `backend/app/bootstrap/registrations/workflow.py` -> audit, forms, workflow, documents, versioned masters.
- `backend/app/bootstrap/registrations/system_admin.py` -> system admin routes.
- `backend/app/bootstrap/registrations/seniority.py` -> seniority routes.
- `backend/app/bootstrap/registrations/leave.py` -> leave routes.
- `backend/app/bootstrap/registrations/pay.py` -> pay routes.
- `backend/app/bootstrap/registrations/identity.py` -> users routes.
- `backend/app/bootstrap/registrations/ess.py` -> ESS routes.
- `backend/app/bootstrap/registrations/service_book.py` -> canonical service book routes.
- `backend/app/bootstrap/registrations/reporting.py` -> reporting and dashboard routes.

Notes:

- Change request routers are included explicitly from `contexts/change_requests/api/router.py`.
- Some contexts (audit, notifications, documents, rbac) are not auto-registered via registration modules but contribute through subscriber wiring or direct router includes.
- `/department/*` routes are owned by `contexts/department`, including the Department-owned sanctioned-strength editor and write API.
- `/departments/manage/*` governance routes remain under `contexts/system_admin/department`, and no longer edit sanctioned strength.

### 2.2.1 Authentication, permissions, and module access

Authentication routes live under:

- `backend/contexts/identity/api/auth_router.py`

The current identity session implementation separates three concepts:

- Authorities/roles: `GLOBAL_DATA_ENTRY`, `DEPT_DATA_ENTRY`, `DEALING_ASSISTANT`, `VERIFIER`, `APPROVING_AUTHORITY`, `SYSTEM_ADMIN`, and related role labels.
- Permissions: action grants such as `PROFILE_CREATE`, `PROFILE_READ_ALL`, `SERVICE_BOOK_READ_ALL`, and `SERVICE_BOOK_ENTRY_CREATE`.
- Module access flags: UI/module visibility ids such as `data_entry`, `service_book`, `leave`, `audit`, `verification`, `approval`, and `attestation`.

`GET /api/auth/module-access` is implemented in:

- `backend/contexts/identity/infrastructure/auth_session_service.py`
- `backend/contexts/identity/domain/module_access_policy.py`

Current behavior:

- In development, missing module configuration falls back to `allow_all`.
- In production, missing module configuration fails closed but infers a safe baseline from the user's authorities and permissions so core role workspaces remain visible.
- If `module_permissions.matrix` exists in system configuration, that matrix is authoritative. Configured `false` values disable inferred baseline modules.
- Module access controls frontend/module visibility and route gates; backend write safety still comes from authorities, permissions, and owning-context guards.

System-admin config validation for `module_permissions` lives in:

- `backend/contexts/system_admin/api/workflow_config_helpers.py`

Regression coverage lives in:

- `backend/tests/test_identity_service_contract.py`
- `backend/tests/test_architecture_guardrails.py`

### 2.3 Context structure (backend)

Primary bounded contexts in `backend/contexts`:

- `audit`
- `change_requests`
- `department`
- `documents`
- `employee_identity`
- `employee_profile`
- `ess`
- `identity`
- `leave`
- `notifications`
- `pay`
- `rbac`
- `reporting`
- `seniority`
- `service_book`
- `system_admin`
- `workflow`

Typical context layering:

- `domain/` for business rules and entities.
- `application/` for use cases and orchestration.
- `infrastructure/` for persistence/adapters.
- `api/` for FastAPI routers and request/response contracts.
- `contracts/` for cross-context events/contracts where needed.

Department-specific note:

- `backend/contexts/department/domain/sanctioned_strength.py` owns sanctioned-strength normalization and validation.
- `backend/contexts/department/repository/department_portal_repo.py` persists Department establishment rows in `department_establishments` and logs mutations in `department_establishment_logs`.
- Legacy `departments.metadata.sanctioned_strength` data is migrated by `backend/scripts/mongodb/backfill_department_establishments.py` and retired by `backend/scripts/mongodb/cleanup_department_establishment_metadata.py`.

### 2.4 Eventing and outbox

Platform eventing components:

- Event bus: `backend/app_platform/event_bus`.
- Outbox: `backend/app_platform/outbox`.
- Contract registry: `backend/app_platform/contracts/registry.py`.
- Registration entrypoint: `backend/app_platform/contracts/events/__init__.py` (imports context-owned schemas and binds them to event names).
- Container wiring: `backend/app/bootstrap/container.py`.
- Subscriber registration: `backend/app/bootstrap/subscribers.py`.

Event payload ownership (Published Language per context):

- Employee identity events → `contexts.employee_identity.contracts.events`
- Service-event lifecycle payloads -> `contexts.service_book.records.contracts.events`
- Document lifecycle payloads → `contexts.documents.contracts.events`
- Only `LenientEventPayload` (domain-neutral primitive) lives in `app_platform.contracts.events.core_events`.

Current subscriber registration includes:

- Audit subscribers (`contexts.audit.application.subscribers`).
- Employee read-model subscribers (`contexts.employee_profile.contracts.subscribers`).
- Notification subscribers (`contexts.notifications.application.subscribers`).
- Service book subscribers (`contexts.service_book.contracts.subscribers`).
- Service book record subscribers (`contexts.service_book.records.contracts.subscribers`).

Guideline: state-changing flows should emit events via outbox-backed paths, not direct ad hoc event publishes from use-case files.

## 3. Frontend Code Map

### 3.1 Frontend entrypoints

- App bootstrap: `frontend/src/index.jsx`.
- Root app component: `frontend/src/App.js`.
- Provider composition: `frontend/src/app/providers/AppProviders.jsx`.

Provider stack currently includes:

- Error boundary.
- Auth context provider.
- Browser router.
- Password gate.
- Toaster notifications.

### 3.2 Route composition

Main route composition:

- `frontend/src/app/router/routes.jsx`

It combines route modules:

- `publicRoutes.jsx`
- `adminRoutes.jsx`
- `departmentRoutes.jsx`
- `employeeRoutes.jsx`
- `essRoutes.jsx`
- `guards.jsx`
- `redirects.jsx`

Routes are lazy-loaded by context page modules and guarded via `ProtectedRoute` with permission checks from identity RBAC model.

Department portal note:

- `frontend/src/app/router/departmentRoutes.jsx` resolves only department-owned page entrypoints under `frontend/src/contexts/department/pages`.
- Department page/model wrappers isolate portal routing from direct employee-profile API and presentation imports.

Employee Directory note:

- The global Employee Directory page is `frontend/src/contexts/employee_identity/pages/EmployeeDirectoryPage.jsx`.
- `Regular Employee` and `Non-Regular Employee` creation actions are shown to `GLOBAL_DATA_ENTRY` and `DEALING_ASSISTANT` users with `PROFILE_CREATE`.
- Those actions intentionally do not depend on the `data_entry` module flag; the create route and backend command still enforce authority and permission.
- Regression coverage is in `frontend/src/contexts/employee_identity/pages/__tests__/EmployeeDirectoryPage.serviceEvents.test.jsx`.

### 3.3 Context structure (frontend)

Main frontend contexts in `frontend/src/contexts` include:

- `access_control`
- `admin`
- `analytics`
- `applications`
- `audit`
- `change_requests`
- `department`
- `documents`
- `employee_identity`
- `employee_profile`
- `ess`
- `forms`
- `identity`
- `leave`
- `masters`
- `notifications`
- `pay`
- `seniority`
- `service_book`
- `workflow`

Boundary rules are defined in `frontend/ARCHITECTURE_BOUNDARIES.md` and enforced by ESLint.

Key constraints:

- App shell/shared layers should use context entrypoints, not direct feature imports.
- Shared layer must remain context-agnostic.

## 4. Request and Data Flow (Simplified)

### 4.1 Backend write path

1. API router receives request.
2. Context application service/use case validates and orchestrates.
3. Context infrastructure repository persists to owned collection.
4. Outbox event is written for state changes.
5. Dispatcher publishes event to subscribers.
6. Other contexts update their own read models/projections.

### 4.2 Frontend page path

1. Route module resolves URL -> page component.
2. `ProtectedRoute` checks auth/permissions.
3. Context page uses context model/api adapters.
4. API call hits backend context router under `/api/*`.

## 5. Where to Add New Code

### 5.1 Backend

When adding a feature in an existing context:

1. Add business rule in context `domain`.
2. Add orchestration in context `application`.
3. Add persistence/adapters in context `infrastructure`.
4. Add/update HTTP contracts in context `api`.
5. Register router only through bootstrap registration modules.
6. Add/adjust events and subscriber wiring if cross-context projection updates are required.

When introducing a new context:

1. Create context package under `backend/contexts/<new_context>`.
2. Keep ownership boundaries explicit.
3. Add registration module under `backend/app/bootstrap/registrations`.
4. Wire router in `router_registry.py`.
5. Add import-boundary and behavior tests.

### 5.2 Frontend

When adding a new screen in existing context:

1. Create page/component under `frontend/src/contexts/<context>`.
2. Add route to the relevant route module in `frontend/src/app/router`.
3. Protect route with `ProtectedRoute` + explicit permissions.
4. Keep shared utilities context-agnostic.

## 6. Guardrails and Validation

Suggested checks after code changes:

- Backend tests (all):
  - `C:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest -q backend/tests`
- Backend boundary tests:
  - `C:/Users/kenne/MyIEMS/.venv/Scripts/python.exe -m pytest backend/tests/test_import_boundaries.py backend/tests/test_authorization_import_guard.py -q`
- Frontend lint and tests:
  - `cd frontend && npm run lint`
  - `cd frontend && npm run test`

## 7. Legacy and Compatibility Notes

- `backend/server.py` exists as a compatibility entrypoint; canonical app wiring is in `backend/app/main.py`.
- `backend/platform/` has been removed; canonical cross-cutting backend infrastructure lives under `backend/app_platform/`.
- Frontend uses `src/app/router/*` as the route composition hub while context feature ownership is enforced by import boundaries.

## 8. Quick Navigation Index

Backend critical files:

- `backend/app/main.py`
- `backend/app/bootstrap/app_factory.py`
- `backend/app/bootstrap/router_registry.py`
- `backend/app/bootstrap/container.py`
- `backend/app/bootstrap/subscribers.py`
- `backend/contexts/*`
- `backend/app_platform/*`

Frontend critical files:

- `frontend/src/index.jsx`
- `frontend/src/App.js`
- `frontend/src/app/providers/AppProviders.jsx`
- `frontend/src/app/router/routes.jsx`
- `frontend/src/app/router/*.jsx`
- `frontend/src/contexts/*`
- `frontend/ARCHITECTURE_BOUNDARIES.md`
