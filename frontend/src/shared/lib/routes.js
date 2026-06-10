/**
 * Route constants registry — single source of truth for all navigable paths.
 *
 * Grouped by feature, not by portal. Every navigate() / Link `to` prop
 * should reference these constants instead of hard-coding path strings.
 */

// ── ESS (Employee Self-Service) ──────────────────────────────────────
export const ESS = {
  HOME:             "/ess",
  DASHBOARD:        "/ess/dashboard",
  PROFILE:          "/ess/profile",
  DOCUMENTS:        "/ess/documents",
  LEAVE:            "/ess/leave",
  SERVICE_BOOK:     "/ess/service-book",
  NOTIFICATIONS:    "/ess/notifications",
  CHANGE_REQUESTS:  "/ess/change-requests",
};

// ── Department Portal ────────────────────────────────────────────────
export const DEPT = {
  HOME:              "/department-portal",
  DASHBOARD:         "/department-portal/dashboard",
  DIRECTORY:         "/department-portal/directory",
  PENDING_WORK:      "/department-portal/pending-work",
  LEAVE:             "/department-portal/leave",
  SANCTIONED_STRENGTH: "/department-portal/sanctioned-strength",
  NEW_IDENTITY:      "/department-portal/employees/new/identity",
  EMPLOYEE:          (id) => `/department-portal/employee/${id}`,
  IDENTITY_EDIT:     (id) => `/department-portal/employee/${id}/identity/edit`,
  PROFILE_EDIT:      (id) => `/department-portal/employee/${id}/profile/edit`,
};

// ── Central Operations Portal (global back-office) ───────────────────
export const OPS = {
  DASHBOARD:        "/portal/dashboard",
  WORK_QUEUE:       "/portal/work",
  EMPLOYEES:        "/portal/employees",
  DOCUMENTS:        "/portal/documents",
  LEAVE:            "/portal/leave",
  AUDIT:            "/portal/audit",
  ANALYTICS:        "/portal/analytics",
  NEW_IDENTITY:     "/portal/employees/new/identity",
  EMPLOYEE:         (id) => `/portal/employees/${id}`,
  IDENTITY_EDIT:    (id) => `/portal/employees/${id}/identity/edit`,
  PROFILE_EDIT:     (id) => `/portal/employees/${id}/profile/edit`,
  SERVICE_BOOK:     "/portal/service-book",
  SERVICE_BOOK_EMP: (id) => `/portal/service-book/${id}`,
  SERVICE_BOOK_OPENING: "/portal/service-book/opening",
  SERVICE_BOOK_OPENING_EMP: (id) => `/portal/service-book/opening/${id}`,
  SERVICE_BOOK_RECORDS: "/portal/service-book/records",
  SERVICE_BOOK_RECORDS_EMP: (id) => `/portal/service-book/records/${id}`,
};

// ── Default / non-portal paths (used by SYSTEM_ADMIN & fallback) ─────
export const MAIN = {
  WORK_QUEUE:       "/work",
  EMPLOYEES:        "/employees",
  DOCUMENTS:        "/documents",
  NEW_IDENTITY:     "/employees/new/identity",
  EMPLOYEE:         (id) => `/employees/${id}`,
  IDENTITY_EDIT:    (id) => `/employees/${id}/identity/edit`,
  PROFILE_EDIT:     (id) => `/employees/${id}/profile/edit`,
  LEAVE:            "/leave",
  AUDITOR:          "/auditor",
  ANALYTICS:        "/analytics",
  SERVICE_BOOK:     "/service-book",
  SERVICE_BOOK_EMP: (id) => `/service-book/${id}`,
  SERVICE_BOOK_OPENING: "/service-book/opening",
  SERVICE_BOOK_OPENING_EMP: (id) => `/service-book/opening/${id}`,
  SERVICE_BOOK_RECORDS: "/service-book/records",
  SERVICE_BOOK_RECORDS_EMP: (id) => `/service-book/records/${id}`,
};

// ── Administration ───────────────────────────────────────────────────
export const ADMIN = {
  HOME:             "/admin",
  MASTERS:          "/admin/masters",
  SENIORITY:        "/seniority",
};

// ── Public / Auth ────────────────────────────────────────────────────
export const AUTH = {
  LOGIN:            "/login",
};

// ── Scope-aware helpers ──────────────────────────────────────────────

/**
 * Return the scope key ("department" | "portal" | "default") from a pathname.
 */
export const scopeFromPath = (pathname = "") => {
  if (pathname.startsWith("/department")) return "department";
  if (pathname.startsWith("/portal/")) return "portal";
  return "default";
};

const SCOPE_MAP = {
  department: { directory: DEPT.DIRECTORY, employee: DEPT.EMPLOYEE, identityCreate: DEPT.NEW_IDENTITY, identityEdit: DEPT.IDENTITY_EDIT, profileEdit: DEPT.PROFILE_EDIT },
  portal:     { directory: OPS.EMPLOYEES,  employee: OPS.EMPLOYEE,  identityCreate: OPS.NEW_IDENTITY,  identityEdit: OPS.IDENTITY_EDIT,  profileEdit: OPS.PROFILE_EDIT },
  default:    { directory: MAIN.EMPLOYEES, employee: MAIN.EMPLOYEE, identityCreate: MAIN.NEW_IDENTITY, identityEdit: MAIN.IDENTITY_EDIT, profileEdit: MAIN.PROFILE_EDIT },
};

/**
 * Build an employee file path scoped to the current portal context.
 */
export const employeeFilePath = (scope, id) => {
  if (!id) return SCOPE_MAP[scope]?.directory ?? MAIN.EMPLOYEES;
  const fn = SCOPE_MAP[scope]?.employee ?? MAIN.EMPLOYEE;
  return fn(id);
};

/** Build the employees directory path for the given scope. */
export const employeeDirectoryPath = (scope) =>
  SCOPE_MAP[scope]?.directory ?? MAIN.EMPLOYEES;

/** Build the "new identity" path for the given scope. */
export const identityCreatePath = (scope) =>
  SCOPE_MAP[scope]?.identityCreate ?? MAIN.NEW_IDENTITY;

/** Build the identity-edit path for the given scope and employee. */
export const identityEditPath = (scope, id) => {
  const fn = SCOPE_MAP[scope]?.identityEdit ?? MAIN.IDENTITY_EDIT;
  return fn(id);
};

/** Build the profile-edit path for the given scope and employee. */
export const profileEditPath = (scope, id) => {
  const fn = SCOPE_MAP[scope]?.profileEdit ?? MAIN.PROFILE_EDIT;
  return fn(id);
};
