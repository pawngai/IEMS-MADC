# Frontend Route Alias Allowlist

This file is the single source of truth for non-canonical frontend route paths
that the runtime still recognizes. Any addition to this list MUST be reviewed.

The CI guardrail
[`frontend/src/app/router/__tests__/routeAliasAllowlist.test.js`](src/app/router/__tests__/routeAliasAllowlist.test.js)
keeps the route files and this allowlist in sync.

## Canonical Path Layers

- `/employees`, `/work`, `/documents`, `/leave`, `/auditor`, `/analytics`, `/admin`, `/seniority`
- `/service-book`, `/service-book/opening`, `/service-book/records`
- `/department-portal/*`
- `/ess/*`

## Allowed Aliases

### `/portal/*` Operations Scope

The OPS route table in [`src/shared/lib/routes.js`](src/shared/lib/routes.js)
exposes `/portal/*` paths that thinly redirect to the canonical paths above.
The aliases remain because the scope is referenced by scope-aware navigation
helpers (`scopeFromPath`, `employeeFilePath`, …) and by tests covering portal
navigation flows.

| Alias | Canonical |
| --- | --- |
| `/portal` | `/portal/dashboard` (canonical landing) |
| `/portal/dashboard` | rendered by `GlobalPortalDashboardPage` |
| `/portal/work` | `/work` |
| `/portal/employees` | `/employees` |
| `/portal/employees/new/identity` | `/employees/new/identity` |
| `/portal/employees/:employeeId` | `/employees/:employeeId` |
| `/portal/employees/:employeeId/identity/edit` | `/employees/:employeeId/identity/edit` |
| `/portal/employees/:employeeId/profile/edit` | `/employees/:employeeId/profile/edit` |
| `/portal/employees/:employeeId/regularisation` | `/employees/:employeeId/regularisation` |
| `/portal/documents` | `/documents` |
| `/portal/leave` | `/leave` |
| `/portal/audit` | `/auditor` |
| `/portal/analytics` | `/analytics` |
| `/portal/service-book` | `/service-book` |
| `/portal/service-book/opening` | `/service-book/opening` |
| `/portal/service-book/opening/:employeeId` | `/service-book/opening/:employeeId` |
| `/portal/service-book/:employeeId` | `/service-book/:employeeId` |
| `/portal/service-book/records` | `/service-book/records` |
| `/portal/service-book/records/:employeeId` | `/service-book/records/:employeeId` |

## Removed Aliases (do not reintroduce)

- `/service-events`, `/service-events/:employeeId` — superseded by `/service-book/records`.
- `/portal/service-events`, `/portal/service-events/:employeeId` — superseded by `/portal/service-book/records`.
- `/department/change-requests`, `/department/employees/...`, `/department/workflow/queue` — superseded by `/department-portal/*`.

The router-import guard
[`routesImportGuard.test.js`](src/app/router/__tests__/routesImportGuard.test.js)
and the allowlist guard fail the build if any removed alias is reintroduced.
