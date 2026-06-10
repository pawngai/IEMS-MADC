# Current Routes Inventory

Generated: 2026-06-11 (Phase 0)

Routes that must keep working (compatibility wrappers) until each phase's
frontend/consumer migration completes.

## Backend API route prefixes (mounted under `/api`)

Source: router `prefix=` declarations + `app/bootstrap/registrations/*`.

| Prefix | Owning context (today) | Target context |
|---|---|---|
| `/auth` | identity | identity_access |
| `/users` | identity | identity_access |
| `/sysadmin`, `/system-admin` | system_admin | system_admin (+ identity_access for RBAC) |
| `/employee-identities` | employee_identity | employee_master |
| `/employee-profiles` | employee_profile | employee_master |
| `/employee-service-summaries` | employee_profile | employee_master / service_book |
| `/ess`, `/ess/change-requests` | ess | portals/ess shell + employee_master/leave_attendance |
| `/department`, `/departments/manage` | department | organization_master + portals/department |
| `/masters` | masters/system_admin | organization_master |
| `/service-book`, `/opening`, `/parts`, `/records`, `/corrections`, `/verification`, `/service-records` | service_book | service_book (unchanged) |
| `/leave` | leave | leave_attendance |
| `/pay` | pay | pay_benefits |
| `/reporting` | reporting | reporting_analytics |
| `/seniority` | seniority | seniority (unchanged) |
| `/workflow` | workflow | workflow (+ change_requests) |
| `/change-requests` | change_requests | workflow/change_requests |
| `/documents` | documents | app_platform/documents |
| `/audit` | audit | app_platform/audit |
| `/forms` | app_platform/forms | app_platform (unchanged) |

**Bootstrap reality:** `app/bootstrap/registrations/` still registers the OLD
context routers (employee_identity, employee_profile, identity, leave, pay,
reporting, department, …). The NEW contexts are not yet wired as routers — they
are contracts-only shims. Route prefixes themselves do **not** change in this
refactor; only the code that owns them moves.

## Frontend route surface

Source of truth: `frontend/src/shared/lib/routes.js` + `app/router/*Routes.jsx`.

### Canonical path layers
`/employees`, `/work`, `/documents`, `/leave`, `/auditor`, `/analytics`,
`/admin`, `/seniority`, `/service-book[/opening|/records]`,
`/department-portal/*`, `/ess/*`.

### Allowlisted aliases (must keep redirecting)
`/portal/*` → canonical (see `frontend/ROUTE_ALIAS_ALLOWLIST.md`).
CI-guarded by `routeAliasAllowlist.test.js` + `routesImportGuard.test.js`.

### Removed aliases (must NOT reappear)
`/service-events*`, `/portal/service-events*`, `/department/change-requests`,
`/department/employees/...`, `/department/workflow/queue`.

### Route module → portal mapping (Phase 3 target)
| Route module | Pages move to |
|---|---|
| `app/router/essRoutes.jsx` | portals/ess (shell), contexts (data) |
| `app/router/departmentRoutes.jsx` | portals/department |
| `app/router/adminRoutes.jsx` | portals/admin |
| `app/router/employeeRoutes.jsx` | stays app/router (cross-portal canonical) |
| `app/router/publicRoutes.jsx` | stays app/router |

## Compatibility-wrapper policy
- Old backend route paths stay identical; the router file becomes a thin import
  from the new context (or the registration points at the moved module).
- Each compatibility wrapper is marked with a `# COMPAT: removable after <phase>`
  comment and listed in the migration report so it can be deleted later.
