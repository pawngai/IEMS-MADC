# IEMS-MADC Context Map

This map records the target bounded contexts and the current migration status.
It is intentionally staged: compatibility adapters may remain only while imports
and route registrations are being migrated safely.

## Final Bounded Contexts

| Context | Owns | Does not own |
| --- | --- | --- |
| `employee_master` | Current employee identity and profile facts, current organizational assignment keys, employee media references. | Historical service events or account/RBAC state. |
| `service_book` | Service history ledger, service records, opening, verification, projections, print/PDF/read-side behavior. | Canonical current employee facts. |
| `organization_master` | Departments, offices, designations, posts, hierarchy, sanctioned strength, reference organizational entities. | Portal-specific workflow or employee profile state. |
| `workflow` | Approvals, verification, submissions, rejections, workflow status transitions. | Domain record storage owned by other contexts. |
| `identity_access` | Users, login identity, roles, permissions, RBAC, portal access, role assignments. | Employee profile enrichment or service history. |
| `leave_attendance` | Leave applications, leave ledger, balances, attendance-facing leave records. | Employee Master current facts or Service Book ledger events. |
| `pay_benefits` | Pay ledger, pay projections, benefits, allowances, pay-related calculations. | Employee Master canonical facts. |
| `reporting_analytics` | Read-only projections, dashboards, analytics, exports. | Source-of-truth domain writes. |
| `app_platform` | Audit, documents, storage, notifications, authorization helpers, event bus/outbox, infrastructure. | Business rules owned by bounded contexts. |

## Cross-Context Access

- Prefer public contracts under `contracts/`, `api/`, `queries/`, `commands/`, or frontend `index.js`.
- Do not import another context's `domain/`, `infrastructure/`, repository, private hook, or private component directly.
- Shared kernel stays primitive-only. Business decisions belong in a bounded context or app platform service.
- Portals compose context UI and public hooks. Portals must not own domain rules.

## Employee Master vs Service Book

- Employee Master is canonical for who the employee currently is.
- Service Book is canonical for what happened in the employee's service history.
- Service Book may read current employee facts only through public Employee Master contracts.
- Employee Master must not store historical service events as a parallel ledger.

## Organization Master

Organization Master is the final owner for departments, offices, designations,
posts, hierarchy, reporting structure, and sanctioned strength. Legacy
`department` and frontend `masters` implementation remains transitional until
imports and route registrations can move without breaking API contracts.

## Identity Access

Identity Access owns accounts, authentication, roles, permissions, authorities,
module access, and portal access. Employee profile data stays in Employee
Master. RBAC must use public employee lookup contracts when employee facts are
required.

## Deprecated Context Names

| Deprecated name | Canonical name | Current status |
| --- | --- | --- |
| `leave` | `leave_attendance` | Backend route registration and frontend app/portal composition use canonical entrypoints; implementation and many context-internal imports still live in `leave`. |
| `pay` | `pay_benefits` | Backend route registration uses the canonical entrypoint; implementation and many imports still live in `pay`. |
| `reporting`, `analytics` | `reporting_analytics` | Backend route registration and frontend app/portal composition use canonical entrypoints; implementation still lives in reporting/analytics modules. |
| `department`, `masters` | `organization_master` | Backend route registration and frontend app/portal composition use canonical entrypoints; implementation still lives in department/masters modules. |

## Route Migration Policy

- Keep public API paths stable unless a route is proven dead by code references and tests.
- When moving an implementation module, keep a thin backward-compatible route alias if clients may still call the old path.
- Document each route move with old module, new module, path change status, and compatibility alias status.

Current route entrypoint status:

| Route area | Old implementation module | Canonical registration module | API path changed | Compatibility alias |
| --- | --- | --- | --- | --- |
| Leave | `contexts.leave.api.router` | `contexts.leave_attendance.api.router` | No, still `/leave` | Canonical router imports legacy implementation temporarily. |
| Pay | `contexts.pay.api.router` | `contexts.pay_benefits.api.router` | No, still `/pay` | Canonical router imports legacy implementation temporarily. |
| Reporting | `contexts.reporting.api.router` | `contexts.reporting_analytics.api.router` | No, still `/reporting` | Canonical router imports legacy implementation temporarily. |
| Department portal | `contexts.department.api.router` | `contexts.organization_master.api.router` | No, still `/department` | Canonical router imports legacy implementation temporarily. |
| Department establishment admin | `contexts.department.api.admin_establishment_router` | `contexts.organization_master.api.admin_establishment_router` | No, existing prefix retained | Canonical router imports legacy implementation temporarily. |

## Large Frontend Files

The current first-pass scan found these high-priority files over 500 lines:

- `frontend/src/contexts/change_requests/containers/EssChangeRequestsScreen.jsx`
- `frontend/src/contexts/service_book/records/components/RecordServiceBookRecordDialog.jsx`
- `frontend/src/contexts/analytics/components/AnalyticsDashboardSections.jsx`
- `frontend/src/contexts/employee_master/pages/EmployeeDirectoryPage.jsx`
- `frontend/src/contexts/employee_master/components/EmployeeProfileExtensionEditor.jsx`
- `frontend/src/contexts/seniority/components/SeniorityListsTab.jsx`

Split these in dedicated behavior-preserving patches. Do not combine large UI
extractions with context import migration.
