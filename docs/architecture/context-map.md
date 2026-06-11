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
posts, hierarchy, reporting structure, and sanctioned strength. The legacy
`department` and frontend `masters` implementations have been absorbed into
`organization_master` on both layers (2026-06-12); the legacy roots are deleted.

## Identity Access

Identity Access owns accounts, authentication, roles, permissions, authorities,
module access, and portal access. Employee profile data stays in Employee
Master. RBAC must use public employee lookup contracts when employee facts are
required.

## Deprecated Context Names

| Deprecated name | Canonical name | Current status |
| --- | --- | --- |
| `leave` | `leave_attendance` | Migration complete (2026-06-12): implementation lives in `leave_attendance` on both layers; legacy root deleted. |
| `pay` | `pay_benefits` | Migration complete (2026-06-12): implementation lives in `pay_benefits` on both layers; legacy root deleted. |
| `reporting`, `analytics` | `reporting_analytics` | Migration complete (2026-06-12): implementation lives in `reporting_analytics` on both layers; legacy roots deleted. |
| `department`, `masters` | `organization_master` | Migration complete (2026-06-12): implementation lives in `organization_master` on both layers; legacy roots deleted. |

## Route Migration Policy

- Keep public API paths stable unless a route is proven dead by code references and tests.
- When moving an implementation module, keep a thin backward-compatible route alias if clients may still call the old path.
- Document each route move with old module, new module, path change status, and compatibility alias status.

Current route entrypoint status:

| Route area | Implementation module | Canonical registration module | API path changed | Compatibility alias |
| --- | --- | --- | --- | --- |
| Leave | `contexts.leave_attendance.api.router` | `contexts.leave_attendance.api.router` | No, still `/leave` | None needed; router owns the implementation. |
| Pay | `contexts.pay_benefits.api.router` | `contexts.pay_benefits.api.router` | No, still `/pay` | None needed; router owns the implementation. |
| Reporting | `contexts.reporting_analytics.api.router` | `contexts.reporting_analytics.api.router` | No, still `/reporting` | None needed; router owns the implementation. |
| Department portal | `contexts.organization_master.api.router` | `contexts.organization_master.api.router` | No, still `/department` | None needed; router owns the implementation. |
| Department establishment admin | `contexts.organization_master.api.admin_establishment_router` | `contexts.organization_master.api.admin_establishment_router` | No, existing prefix retained | None needed; router owns the implementation. |

## Large Frontend Files

Completed first-pass splits:

- `frontend/src/contexts/change_requests/containers/EssChangeRequestsScreen.jsx`
- `frontend/src/contexts/service_book/records/components/RecordServiceBookRecordDialog.jsx`
- `frontend/src/contexts/reporting_analytics/components/AnalyticsDashboardSections.jsx`
- `frontend/src/contexts/leave_attendance/pages/LeaveDashboardPage.jsx`
- `frontend/src/contexts/employee_master/pages/EmployeeDirectoryPage.jsx`
- `frontend/src/contexts/employee_master/components/EmployeeProfileExtensionEditor.jsx`
- `frontend/src/contexts/seniority/components/SeniorityListsTab.jsx`
- `frontend/src/contexts/employee_master/components/EmployeeProfileSummary.jsx`

Current high-priority production files over 500 lines:

- `frontend/src/contexts/leave_attendance/pages/EssLeavePage.jsx`
- `frontend/src/portals/ess/pages/EssDashboardPage.jsx`
- `frontend/src/contexts/service_book/records/model/recordServiceBookRecordDialogModel.js`
- `frontend/src/index.css`
- `frontend/src/contexts/employee_master/components/EmployeeProfileExtensionEditor.support.jsx`
- `frontend/src/contexts/workflow/containers/WorkflowQueueScreen.jsx`
- `frontend/src/contexts/workflow/components/WorkflowDetailPanel.jsx`
- `frontend/src/contexts/employee_master/hooks/useEmployeeDirectory.js`
- `frontend/src/contexts/organization_master/pages/DeptSanctionedStrengthPage.jsx`
- `frontend/src/app/layout/Layout.jsx`
- `frontend/src/contexts/applications/pages/GlobalPortalDashboardPage.jsx`
- `frontend/src/contexts/reporting_analytics/pages/AnalyticsDashboardPage.jsx`
- `frontend/src/portals/ess/pages/EssDocumentsPage.jsx`

Split these in dedicated behavior-preserving patches. Do not combine large UI
extractions with context import migration.
