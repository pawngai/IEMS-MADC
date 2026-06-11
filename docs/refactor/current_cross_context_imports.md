# Current Cross-Context Imports

Generated: 2026-06-11 (Phase 0)

## Backend — boundary status: CLEAN (contracts-only)

Grep for any context importing another context's internals
(`api|application|domain|repository|schemas|services|infrastructure|read_model`):

```
from contexts\.\w+\.(api|application|domain|...)   →  0 matches
```

**No backend context reaches past another context's `.contracts`.** The
contracts-only boundary rule already holds. This is the foundation the shim
strategy is built on.

### Cross-context `.contracts` dependency graph (consumer → provider, by count)

| Provider contracts | Imported by (count) |
|---|---|
| identity_access.contracts | 109 |
| employee_master.contracts | 36 |
| employee_profile.contracts | 29 |
| service_book.contracts | 25 |
| leave.contracts | 16 |
| identity.contracts | 15 |
| pay.contracts | 12 |
| employee_identity.contracts | 11 |
| documents.contracts | 9 |
| leave_attendance.contracts | 7 |
| change_requests.contracts | 7 |
| notifications.contracts | 6 |
| rbac.contracts | 4 |
| audit.contracts | 3 |
| pay_benefits.contracts | 1 |

**Mid-flight observation:** consumers already import the NEW contract names
(identity_access 109, employee_master 36, leave_attendance 7, pay_benefits 1) as
well as the OLD ones (identity 15, employee_identity 11, employee_profile 29,
leave 16, pay 12, rbac 4). The new contracts re-export the old, so both resolve.
**Migration finishes by moving implementations under the new contracts and
deleting the old contract modules** (replacing remaining old-name imports first).

### app_platform → contexts imports (boundary concern)

app_platform should be domain-neutral but currently imports:
```
from contexts.identity_access.rbac            ×6     → becomes app_platform/authorization
from contexts.documents       ×3     → documents moves INTO app_platform
from contexts.service_book    ×2     → REVIEW: platform should not need a context
from contexts.identity_access ×2     → becomes app_platform/authorization
from contexts.employee_master.identity ×1   → REVIEW
```
Tracked in risk register R-7. Most resolve naturally when rbac→authorization and
documents/audit/notifications move into app_platform (Phase 6).

## Frontend — boundary status: enforced by eslint + tests

Guards already in place:
- `frontend/eslint.config.js` — restricted imports across shared/platform/app/
  portal/context layers.
- `frontend/src/contexts/__tests__/contextBoundary.test.js` — context↔context
  allowlist; shared/UI restrictions.
- `frontend/src/app/router/__tests__/routesImportGuard.test.js`.

### New-context frontend shims (re-export façades)
All former shims have been absorbed: `leave_attendance`, `pay_benefits`,
`organization_master`, and `reporting_analytics` now own their implementations
directly (the legacy `leave`, `pay`, `department`, `masters`, and `analytics`
contexts were deleted).
**Phase rule:** a context may import another only through `@/contexts/<name>`;
portals only through public `@/contexts/<name>`; `shared`/`platform` never import
contexts or portals; contexts never import portals.

## Verification commands (re-runnable)
```bash
# backend: must stay 0
grep -rE "from contexts\.\w+\.(api|application|domain|repository|schemas|services|infrastructure|read_model)" backend/contexts --include=*.py

# frontend boundary tests
cd frontend && npm test -- contextBoundary routesImportGuard
```
