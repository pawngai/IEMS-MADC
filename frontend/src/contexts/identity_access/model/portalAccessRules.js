/**
 * Identity Access — portal access rules.
 *
 * Centralizes which portal/landing a user may enter based on authorities,
 * permissions, and module access. Relocated from app/router/defaultLanding.js so
 * portal-access policy lives in identity_access (RBAC + portal access centralized).
 */
import { Permissions } from "@/platform/permissions";
import { ADMIN, AUTH, DEPT, ESS, MAIN, OPS } from "@/shared/lib/routes";

const EMPLOYEE_AUTHORITIES = new Set(["EMPLOYEE"]);
const DEPARTMENT_AUTHORITIES = new Set(["DEPT_DATA_ENTRY", "HOD"]);
const WORK_QUEUE_AUTHORITIES = new Set([
  "GLOBAL_DATA_ENTRY",
  "DEALING_ASSISTANT",
  "SECTION_OFFICER",
  "VERIFIER",
  "NODAL_OFFICER",
  "DDO",
  "APPROVING_AUTHORITY",
  "APPOINTING_AUTHORITY",
  "DISCIPLINARY_AUTHORITY",
]);

const GLOBAL_DIRECTORY_PERMISSIONS = [
  Permissions.PROFILE_READ_ALL,
  Permissions.PROFILE_CREATE,
  Permissions.PROFILE_UPDATE_ALL,
  Permissions.SERVICE_BOOK_READ_ALL,
  Permissions.SERVICE_BOOK_ENTRY_CREATE,
];

const ESS_PORTAL_PERMISSIONS = [
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

  const hasNonEmployeeAuthority = authorities.some((authority) => authority !== "EMPLOYEE");
  const canEssPortal = canEnterEssPortal({ user, canAny, canAccessEssPortal });
  const essHomePath = getEssHomePath({ can });
  const canAdminPortal =
    primaryAuthority === "SYSTEM_ADMIN" &&
    can(Permissions.USER_MANAGEMENT) &&
    can(Permissions.SYSTEM_CONFIG) &&
    canAccessModule("admin_console");
  const canDepartmentPortal =
    authorities.some((authority) => DEPARTMENT_AUTHORITIES.has(authority)) &&
    can(Permissions.PROFILE_READ_ALL);
  const canGlobalDirectory =
    hasNonEmployeeAuthority &&
    canAny(GLOBAL_DIRECTORY_PERMISSIONS);
  const canGlobalLeave =
    hasNonEmployeeAuthority &&
    (can(Permissions.LEAVE_RECOMMEND) || can(Permissions.LEAVE_SANCTION)) &&
    canAccessModule("leave");
  const canAudit =
    hasNonEmployeeAuthority &&
    can(Permissions.AUDIT_READ_ALL) &&
    canAccessModule("audit");
  const canAnalytics = hasNonEmployeeAuthority && can(Permissions.PROFILE_READ_ALL);
  const canSeniority = authorities.some((authority) =>
    ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "VERIFIER", "APPROVING_AUTHORITY", "SYSTEM_ADMIN"].includes(authority)
  );

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
  if (hasNonEmployeeAuthority && authorities.some((authority) => WORK_QUEUE_AUTHORITIES.has(authority))) {
    return OPS.WORK_QUEUE;
  }
  if (canGlobalLeave) return OPS.LEAVE;
  if (canAudit) return OPS.AUDIT;
  if (canAnalytics) return OPS.ANALYTICS;
  if (canSeniority) return ADMIN.SENIORITY;
  if (canEssPortal) return essHomePath;

  return null;
};
