# MyIEMS Product Requirements And Current Implementation

## Product Goal

MyIEMS is the MADC Human Resource Management System. It manages employee identity, profile enrichment, department workflows, service records, leave, pay-related records, seniority, documents, audit history, reporting, and employee self-service.

The product must remain suitable for government HR operations:

- strict bounded-context ownership
- authority-based access control
- department and employee scoping
- immutable audit trails
- regular-employee-only Service Book behavior
- document metadata that supports workflows without becoming domain truth
- read-only reporting over canonical context collections

## Current Runtime Shape

- Backend: FastAPI + MongoDB modular monolith
- Frontend: React + Vite
- Backend entrypoint: `backend/app/main.py`
- Frontend entrypoint: `frontend/src/index.jsx`
- Backend API base: `/api`
- Health endpoints: `/health/live` and `/health/ready`
- Frontend route composition: `frontend/src/app/router`
- Frontend provider composition: `frontend/src/app/providers`
- Runtime configuration: project-root `.env` loaded by `backend/app_platform/config/settings.py`

## Backend Bounded Contexts

Current backend contexts under `backend/contexts`:

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

There is no standalone `service_events` context. Current service-history mutation behavior lives under `backend/contexts/service_book/records`; legacy service-event terminology remains only in event names, compatibility schemas, and API wording where needed.

## Frontend Contexts

Current frontend contexts under `frontend/src/contexts`:

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

Service record UI lives under `frontend/src/contexts/service_book/records`.

## Core Ownership Rules

- EmployeeIdentity owns canonical employee identity: employee code, name, date of birth, employment type, and identity workflow.
- EmployeeProfile owns profile enrichment and read projections.
- Department owns department portal orchestration and Department-scoped sanctioned-strength establishment records.
- ServiceBook owns Service Book opening, official service records, records workflow, read-side projections, corrections, verification, and print/PDF surfaces.
- Leave owns leave applications and leave ledger behavior.
- Pay owns pay and financial ledger behavior.
- Documents owns file storage, document metadata, document lifecycle events, and document boundary validation.
- Audit owns immutable audit entries.
- Reporting is read-only and aggregates canonical context collections.
- Workflow owns process/task state and must not own domain truth payloads.
- `shared_kernel` contains primitives only.

## User And Portal Requirements

### Admin And Operations

Current operational surfaces:

- `/employees`
- `/employees/:employeeId`
- `/documents`
- `/work`
- `/service-book`
- `/service-book/opening`
- `/service-book/records`
- `/leave`
- `/auditor`
- `/analytics`
- `/admin`
- `/seniority`

### Department Portal

Current department surfaces:

- `/department-portal/dashboard`
- `/department-portal/directory`
- `/department-portal/pending-work`
- `/department-portal/leave`
- `/department-portal/sanctioned-strength`
- `/department-portal/employee/:employeeId`

### Employee Self-Service

Current ESS surfaces:

- `/ess/dashboard`
- `/ess/profile`
- `/ess/documents`
- `/ess/service-book`
- `/ess/leave`
- `/ess/notifications`
- `/ess/change-requests`

## Implemented Functional Areas

### Identity And Access

- Login, refresh, logout, current-user lookup, module access, RBAC matrix, and password change routes live under `/api/auth`.
- User management and employee-account provisioning live under `/api/users`.
- Refresh tokens are transported via HttpOnly cookies.
- Frontend requests include bearer access tokens and optional active-role headers through `frontend/src/platform/api/httpClient.js`.
- Authorities/roles, permissions, and module visibility are separate concepts. `data_entry` is a module id, not a role or permission.
- Production module access infers a safe baseline only when module config is absent; configured `module_permissions.matrix` is authoritative when present.
- Global Employee Directory create actions for regular and non-regular employees require an allowed data-entry authority plus `PROFILE_CREATE`, and do not depend on the `data_entry` module flag.

### Employee Identity

- Canonical employee identity is managed through `employee_identity`.
- Employee creation/editing flows are surfaced through employee and department routes.
- Identity normalization and service-book eligibility rules are owned by the identity domain.

### Employee Profile

- Profile enrichment is managed through `employee_profile`.
- Profile views compose identity and profile data without moving canonical truth into profile-owned records.
- Profile workflow and read models support employee file and department portal views.

### Department

- Department portal routes are mounted under `/api/department`.
- Department owns dashboard, employee directory/snapshot, pending work, pending leaves, activity, and sanctioned-strength read/write behavior.
- Department governance CRUD remains under SystemAdmin at `/api/departments/manage`.

### Service Book And Service Book Records

- Service Book applies only to regular employees.
- Service Book opening, part views, query/read-side behavior, verification, corrections, print/PDF surfaces, and official records live under `service_book`.
- Service Book Records provide the current service-history mutation lifecycle.
- Legacy frontend `/service-events` routes redirect to `/service-book/records`.

### Documents

- Documents routes are mounted under `/api/documents`.
- Documents own photo, signature, generic document upload, document list, metadata, download, and delete behavior.
- Document metadata can link to entities but must not carry service-history truth.
- Local storage is the default; GCS-backed storage is available through document storage settings.

### Leave

- Leave routes are mounted under `/api/leave`.
- Leave supports ESS and operational views, applications, workflow visibility, and document attachment behavior.

### Pay

- Pay routes are mounted under `/api/pay`.
- Pay owns pay-related ledger behavior and emits events for downstream projections/audit where applicable.

### Audit

- Audit owns immutable audit trail behavior.
- The current implementation has an auditor dashboard under `frontend/src/contexts/audit/pages/AuditorDashboardPage.jsx`.
- Historical AI audit-agent endpoint descriptions are not part of the current runtime baseline.

### Reporting And Analytics

- Reporting routes are mounted under `/api/reporting`.
- Reporting is read-only and provides analytics overview, workforce, leave, workflow, service-events/service-record summaries, and CSV drilldown export.

### Seniority

- Seniority owns generated seniority lists and rank override workflows.
- Frontend seniority UI lives under `frontend/src/contexts/seniority`.

## Architecture Guardrails

The implementation is protected by tests and lint rules, including:

- `backend/tests/test_import_boundaries.py`
- `backend/tests/test_context_boundaries.py`
- `backend/tests/test_context_isolation_whole_repo.py`
- `backend/tests/test_target_architecture_enforcement.py`
- `backend/tests/test_cross_context_collection_isolation.py`
- `backend/tests/test_collection_ownership_enforced.py`
- `backend/tests/test_frontend_feature_architecture.py`
- `frontend/src/contexts/__tests__/contextBoundary.test.js`
- `frontend/src/app/router/__tests__/routesImportGuard.test.js`
- `frontend/eslint.config.js`

## Deployment Requirements

The current supported deployment shape is:

- Firebase Hosting for the Vite frontend
- Compute Engine VM for backend, MongoDB, and Caddy
- Docker Compose on the VM
- Prebuilt backend image promoted through GitHub Actions or helper scripts

Current deployment docs live in `docs/reference/google-cloud-deployment.md`.

## Non-Goals In Current Runtime

- A standalone `service_events` bounded context is not part of the current implementation.
- Historical `features/audit`, `features/admin`, and `features/workQueue` page paths are not current UI entrypoints.
- Historical `/api/audit-agent/*` AI audit endpoints are not part of the current runtime baseline.
- `backend/platform/*` is not part of the current backend runtime.

## Migration Summary

- This PRD has been refreshed from an older implementation narrative to the current bounded-context runtime.
- Old feature-path, audit-agent, service-events-context, and backend-platform references have been replaced with the current context and route structure.
- The document now treats Service Book Records as the current service-history mutation surface.

## Risk List

- This PRD is a product baseline, not a route-by-route API contract. Integration changes must still be checked against context routers, frontend API adapters, and regression tests.
- Work Queue is an orchestration surface only. It must preserve each source context's workflow status instead of deriving Draft/Submitted/Verified state from identity status, document metadata, or UI labels.
- Service Book and Service Book Records remain regular-employee-only. Work Queue, analytics, and reporting changes must not reintroduce service-book work items for non-regular employees.
- Service-event wording appears in compatibility routes, event names, scripts, and some schemas. It does not indicate a standalone `service_events` bounded context or a separate owner for service-history mutations.
- Route, context, deployment, auth, or workflow-stage changes must update this PRD, the README, and the relevant reference doc in the same change set.
