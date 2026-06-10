# Refactor Risk Register

Generated: 2026-06-11 (Phase 0). Severity: H/M/L. Status updated each phase.

## Context: this is a MID-FLIGHT migration

The repo already contains target contexts as **shim layers** (new
`*/contracts/` backend modules and `*/index.js` frontend façades that re-export
old implementations). The running app's bootstrap still wires the OLD context
routers. The work remaining is to relocate implementations into the new contexts
and retire the old folders + old contract modules. This shapes every risk below.

| ID | Risk | Sev | Mitigation | Status |
|---|---|---|---|---|
| R-1 | Field loss merging employee_identity + employee_profile | H | Phase 0 field inventory + mapping; `legacy_fields` catch-all; Phase 9 migration report asserts unmapped=0 | OPEN |
| R-2 | `address_line1/line2` (write path) vs `address` (model) mismatch silently drops address data | H | employee_master ContactDetails declares both forms; migration backfills; see mapping §B | OPEN |
| R-3 | 35 employment-type fields persisted but undeclared → lost if model uses `extra="forbid"` | H | Declare all 35 as optional employee_master fields (mapping §C); never forbid-strip them | OPEN |
| R-4 | Two `ContactDetails` definitions (identity value_objects.py + profile profile_model.py) diverge | M | Unify into one employee_master value object; assert field-set equality in test | OPEN |
| R-5 | Both old + new contract names imported across backend (109 identity_access, 15 identity, etc.) | M | Replace remaining old-name imports BEFORE deleting old contracts; grep gate in CI | OPEN |
| R-6 | Bootstrap wires old routers; moving impl could unregister routes / 404 the app | H | Keep route prefixes identical; flip registration to new module only after import smoke passes; verify with live-browser login each phase | OPEN |
| R-7 | app_platform imports contexts (rbac×6, documents×3, service_book×2, identity_access×2, employee_identity×1) violating platform neutrality | M | rbac→app_platform/authorization, documents/audit/notifications→app_platform (Phase 6); review service_book/employee_identity couplings individually | OPEN |
| R-8 | identity_access is contracts-only; merging identity+rbac impl is large (user_management_service 749L, policy_engine 670L, models 496L) | M | Move in sub-steps: users/sessions, then roles/permissions, then module/portal access; keep `/auth` + `/users` prefixes | OPEN |
| R-9 | AuthContext minimization may break consumers reading removed fields | M | Inventory AuthContext consumers first; expose removed data via permissionSelectors; keep `user, loading, login, logout, activeRole, setActiveRole, moduleAccess` | OPEN |
| R-10 | Portal moves (ESS/Dept/Admin → portals/) break deep imports & lazy route paths | M | Move shells only; data stays in contexts; update router lazy imports; portals import contexts via index.js only | OPEN |
| R-11 | department split (organization_master master-data vs portals/department UI) entangled with system_admin/department + masters | M | Map department endpoints (`/department`, `/departments/manage`, `/masters`) to owner before moving; establishment aggregate → organization_master | OPEN |
| R-12 | change_requests → workflow merge may collide with ess/change-requests routes | L | Keep `/change-requests` + `/ess/change-requests` prefixes; move under workflow/change_requests namespace | OPEN |
| R-13 | Migration backfill script run against prod-shaped data with unexpected keys | M | Idempotent upsert keyed on employee_id; dry-run mode; legacy_fields catch-all; report counts | OPEN |
| R-14 | Large-file splits introduce behavior regressions | L | Split after relocation; pure mechanical extraction; rely on existing tests + new field/route tests | OPEN |
| R-15 | Windows + Python 3.14 + Mongo local env; tests may be env-sensitive | M | Run `pytest` import-boundary/architecture suites after each phase; live-browser smoke (login global.dataentry) as end-to-end gate | OPEN |
| R-16 | Frontend `masters` + `applications` + `access_control` contexts not in target list — ownership unclear | M | Decide: masters→organization_master, access_control→identity_access, applications→portals/admin or reporting_analytics; confirm with stakeholder before deleting | OPEN |

## Hard gates before any deletion (per spec)
1. All employee_identity + employee_profile fields mapped (R-1/2/3 closed).
2. Old contract modules have zero remaining importers (R-5 closed).
3. App builds; existing tests pass; live-browser login works (R-6/15).
4. Migration report proves unmapped=0, dropped=0 (R-1).

## Phasing principle
Incremental, app-working-after-each-phase, safe commit per phase. Order:
P1 employee_master → P2 identity_access → P3 portals → P4 renames
(leave_attendance/pay_benefits/reporting_analytics) → P5 organization_master split
→ P6 platform moves (documents/audit/notifications) + change_requests→workflow →
P7 boundary tests → P8 large-file splits → P9 migration report.

## Open questions for stakeholder (R-16)
- `frontend/src/contexts/masters` ownership → organization_master?
- `frontend/src/contexts/access_control` → identity_access?
- `frontend/src/contexts/applications` (GlobalPortalDashboard) → portals/admin?
- `backend/contexts/reporting` vs `analytics`: spec says merge both into
  reporting_analytics, but backend has only `reporting` (no `analytics` backend
  context). Confirm analytics is frontend-only.
