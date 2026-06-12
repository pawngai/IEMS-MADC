/**
 * Identity Access — portal access rules.
 *
 * Single source of truth for portal/workspace capabilities. Every permission
 * combination or authority list that gates a portal area is defined here once
 * and consumed by the router guards, the Layout navigation, dashboards, and
 * the default-landing decision table. Do not copy these lists into components.
 */
import { DEPARTMENT_SCOPED_AUTHORITIES, Permissions } from "@/platform/permissions";
import { ADMIN, AUTH, DEPT, ESS, MAIN, OPS } from "@/shared/lib/routes";

const EMPLOYEE_AUTHORITIES = new Set(["EMPLOYEE"]);
const DEPARTMENT_AUTHORITIES = new Set(DEPARTMENT_SCOPED_AUTHORITIES);

export const WORK_QUEUE_AUTHORITIES = [
  "GLOBAL_DATA_ENTRY",
  "DEALING_ASSISTANT",
  "SECTION_OFFICER",
  "VERIFIER",
  "NODAL_OFFICER",
  "DDO",
  "APPROVING_AUTHORITY",
  "APPOINTING_AUTHORITY",
  "DISCIPLINARY_AUTHORITY",
];
const WORK_QUEUE_AUTHORITY_SET = new Set(WORK_QUEUE_AUTHORITIES);

export const SENIORITY_AUTHORITIES = [
  "SYSTEM_ADMIN",
  "GLOBAL_DATA_ENTRY",
  "DEALING_ASSISTANT",
  "VERIFIER",
  "APPROVING_AUTHORITY",
];

export const GLOBAL_DIRECTORY_PERMISSIONS = [
  Permissions.PROFILE_READ_ALL,
  Permissions.PROFILE_CREATE,
  Permissions.PROFILE_UPDATE_ALL,
  Permissions.SERVICE_BOOK_READ_ALL,
  Permissions.SERVICE_BOOK_ENTRY_CREATE,
];

export const ESS_PORTAL_PERMISSIONS = [
  Permissions.DOCUMENT_READ_OWN,
  Permissions.PROFILE_READ_OWN,
  Permissions.SERVICE_BOOK_READ_OWN,
  Permissions.LEAVE_APPLY_OWN,
  Permissions.LEAVE_READ_OWN,
  Permissions.PROFILE_UPDATE_OWN_LIMITED,
  Permissions.PROFILE_UPDATE_ALL,
];

const normalizeAuthorities = (user) =>
  Array.from(new Set(Array.isArray(user?.authorities) ? user.authorities.filter(Boolean) : []));

const hasNonEmployeeAuthority = (user) =>
  normalizeAuthorities(user).some((authority) => authority !== "EMPLOYEE");

/** SYSTEM_ADMIN with both governance permissions and the console module. */
export const canAccessAdminConsole = ({ can, canAccessModule, getPrimaryAuthority }) =>
  getPrimaryAuthority?.() === "SYSTEM_ADMIN" &&
  Boolean(can?.(Permissions.USER_MANAGEMENT)) &&
  Boolean(can?.(Permissions.SYSTEM_CONFIG)) &&
  Boolean(canAccessModule?.("admin_console"));

/** Department-scoped authority (HOD / DEPT_DATA_ENTRY) with directory read. */
export const canAccessDepartmentPortal = ({ user, can }) =>
  normalizeAuthorities(user).some((authority) => DEPARTMENT_AUTHORITIES.has(authority)) &&
  Boolean(can?.(Permissions.PROFILE_READ_ALL));

/** Any non-employee role holding a global directory permission. */
export const canAccessGlobalDirectory = ({ user, canAny }) =>
  hasNonEmployeeAuthority(user) && Boolean(canAny?.(GLOBAL_DIRECTORY_PERMISSIONS));

/** Leave workflow access for operations users (module-gated). */
export const canAccessGlobalLeave = ({ user, can, canAccessModule }) =>
  hasNonEmployeeAuthority(user) &&
  (Boolean(can?.(Permissions.LEAVE_RECOMMEND)) || Boolean(can?.(Permissions.LEAVE_SANCTION))) &&
  Boolean(canAccessModule?.("leave"));

/** Audit log access (module-gated). */
export const canAccessAudit = ({ can, canAccessModule }) =>
  Boolean(can?.(Permissions.AUDIT_READ_ALL)) && Boolean(canAccessModule?.("audit"));

/** Workforce analytics access. */
export const canAccessAnalytics = ({ can }) => Boolean(can?.(Permissions.PROFILE_READ_ALL));

/** Seniority list management. */
export const canManageSeniority = ({ user }) =>
  normalizeAuthorities(user).some((authority) => SENIORITY_AUTHORITIES.includes(authority));

export const getEssHomePath = ({ can }) => {
  if (can(Permissions.PROFILE_READ_OWN) || can(Permissions.SERVICE_BOOK_READ_OWN)) {
    return ESS.DASHBOARD;
  }
  if (can(Permissions.PROFILE_READ_ALL)) {
    return ESS.PROFILE;
  }
  if (can(Permissions.DOCUMENT_READ_OWN)) {
    return ESS.DOCUMENTS;
  }
  if (can(Permissions.LEAVE_APPLY_OWN) || can(Permissions.LEAVE_READ_OWN)) {
    return ESS.LEAVE;
  }
  return ESS.DASHBOARD;
};

export const canEnterEssPortal = ({ user, canAny, canAccessEssPortal }) => {
  const authorities = normalizeAuthorities(user);
  return (
    authorities.some((authority) => EMPLOYEE_AUTHORITIES.has(authority)) &&
    Boolean(user?.employee_id) &&
    Boolean(canAccessEssPortal?.()) &&
    Boolean(canAny?.(ESS_PORTAL_PERMISSIONS))
  );
};

export const getDefaultLandingPath = ({
  user,
  can,
  canAny,
  canAccessModule,
  canAccessEssPortal,
  getPrimaryAuthority,
}) => {
  if (!user) {
    return AUTH.LOGIN;
  }

  const authorities = normalizeAuthorities(user);
  const primaryAuthority = typeof getPrimaryAuthority === "function"
    ? getPrimaryAuthority()
    : authorities[0] || "EMPLOYEE";

  const canEssPortal = canEnterEssPortal({ user, canAny, canAccessEssPortal });
  const essHomePath = getEssHomePath({ can });
  const canAdminPortal = canAccessAdminConsole({ can, canAccessModule, getPrimaryAuthority });
  const canDepartmentPortal = canAccessDepartmentPortal({ user, can });
  const canGlobalDirectory = canAccessGlobalDirectory({ user, canAny });
  const canGlobalLeave = canAccessGlobalLeave({ user, can, canAccessModule });
  const canAudit = hasNonEmployeeAuthority(user) && canAccessAudit({ can, canAccessModule });
  const canAnalytics = hasNonEmployeeAuthority(user) && canAccessAnalytics({ can });
  const canSeniority = canManageSeniority({ user });

  switch (primaryAuthority) {
    case "SYSTEM_ADMIN":
      if (canAdminPortal) return ADMIN.HOME;
      if (canGlobalDirectory) return MAIN.EMPLOYEES;
      if (canAudit) return MAIN.AUDITOR;
      if (canAnalytics) return MAIN.ANALYTICS;
      if (canSeniority) return ADMIN.SENIORITY;
      break;
    case "HOD":
    case "DEPT_DATA_ENTRY":
      if (canDepartmentPortal) return DEPT.DASHBOARD;
      break;
    case "GLOBAL_DATA_ENTRY":
    case "DEALING_ASSISTANT":
      if (canGlobalDirectory) return OPS.EMPLOYEES;
      return OPS.WORK_QUEUE;
    case "AUDITOR":
      if (canAudit) return OPS.AUDIT;
      break;
    case "VERIFIER":
    case "APPROVING_AUTHORITY":
    case "SECTION_OFFICER":
    case "NODAL_OFFICER":
    case "DDO":
    case "APPOINTING_AUTHORITY":
    case "DISCIPLINARY_AUTHORITY":
      return OPS.WORK_QUEUE;
    case "EMPLOYEE":
      if (canEssPortal) return essHomePath;
      break;
    default:
      break;
  }

  if (canAdminPortal) return ADMIN.HOME;
  if (canDepartmentPortal) return DEPT.DASHBOARD;
  if (canGlobalDirectory) return OPS.EMPLOYEES;
  if (hasNonEmployeeAuthority(user) && authorities.some((authority) => WORK_QUEUE_AUTHORITY_SET.has(authority))) {
    return OPS.WORK_QUEUE;
  }
  if (canGlobalLeave) return OPS.LEAVE;
  if (canAudit) return OPS.AUDIT;
  if (canAnalytics) return OPS.ANALYTICS;
  if (canSeniority) return ADMIN.SENIORITY;
  if (canEssPortal) return essHomePath;

  return null;
};
