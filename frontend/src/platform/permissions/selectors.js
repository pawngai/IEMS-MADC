import { Authorities, Permissions } from "./constants";
import { AUTHORITY_DISPLAY_NAMES, AUTHORITY_PRIORITY } from "./authorityMeta";

export const GLOBAL = "GLOBAL";
export const DEPARTMENT = "DEPARTMENT";
export const EMPLOYEE = "EMPLOYEE";

export const DEPARTMENT_SCOPED_AUTHORITIES = ["DEPT_DATA_ENTRY", "HOD"];
export const GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES = ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"];
export const DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES = ["DEPT_DATA_ENTRY"];

const DEPARTMENT_AUTHORITIES = new Set(DEPARTMENT_SCOPED_AUTHORITIES);

const normalizeAuthorityValues = (authorities) => {
  const source = Array.isArray(authorities) ? authorities : authorities ? [authorities] : [];
  return new Set(
    source
      .map((value) => String(value || "").trim().toUpperCase())
      .filter(Boolean),
  );
};

export const isDepartmentScopedRole = (role) =>
  DEPARTMENT_AUTHORITIES.has(String(role || "").trim().toUpperCase());

export const normalizeAuthorities = (authorities) => {
  const normalized = normalizeAuthorityValues(authorities);
  if (normalized.size === 0) normalized.add("EMPLOYEE");
  return normalized;
};

export const getUserAuthorities = (user) =>
  normalizeAuthorities(user?.authorities || user?.authority || []);

export const hasAuthority = (user, authority) =>
  getUserAuthorities(user).has(String(authority || "").trim().toUpperCase());

export const hasAnyAuthority = (user, authorities = []) =>
  (authorities || []).some((authority) => hasAuthority(user, authority));

export const assignRole = (currentRoles = [], role) => {
  const normalized = currentRoles
    .map((item) => String(item || "").trim().toUpperCase())
    .filter(Boolean);
  const next = [...new Set(normalized)];
  const roleKey = String(role || "").trim().toUpperCase();
  if (roleKey && !next.includes(roleKey)) next.push(roleKey);
  return next;
};

export const revokeRole = (currentRoles = [], role) => {
  const roleKey = String(role || "").trim().toUpperCase();
  return currentRoles
    .map((item) => String(item || "").trim().toUpperCase())
    .filter((item) => item && item !== roleKey);
};

const getUserDepartmentCode = (user) => {
  const code = String(user?.department_code || user?.department_id || "").trim().toUpperCase();
  return code || null;
};

const isOwner = (user, targetEmployeeId) => {
  const callerEmployeeId = String(user?.employee_id || "").trim();
  const target = String(targetEmployeeId || "").trim();
  return Boolean(callerEmployeeId && target && callerEmployeeId === target);
};

export const resolveUserPermissions = (user) => {
  const explicit = Array.isArray(user?.permissions)
    ? user.permissions
    : user?.permissions
      ? [user.permissions]
      : [];
  return new Set(explicit.map((permission) => String(permission).trim()).filter(Boolean));
};

export const resolveScopeAccess = (
  user,
  { targetEmployeeId, targetDepartmentCode, userDepartmentCode } = {},
) => {
  const authorities = normalizeAuthorityValues(user?.authorities || user?.authority || []);
  let scope = GLOBAL;

  if ([...authorities].every((authority) => authority === "EMPLOYEE")) {
    scope = EMPLOYEE;
  } else if ([...authorities].some((authority) => DEPARTMENT_AUTHORITIES.has(authority))) {
    scope = DEPARTMENT;
  }

  if (scope === GLOBAL) return { scope: GLOBAL, allowed: true, reason: "GLOBAL scope" };

  if (scope === DEPARTMENT) {
    const actorDepartment = String(userDepartmentCode || getUserDepartmentCode(user) || "").trim().toUpperCase();
    const targetDepartment = String(targetDepartmentCode || "").trim().toUpperCase();
    if (!actorDepartment) {
      return { scope: DEPARTMENT, allowed: false, reason: "DEPARTMENT scope requires caller department mapping" };
    }
    if (targetDepartment && actorDepartment !== targetDepartment) {
      return { scope: DEPARTMENT, allowed: false, reason: "DEPARTMENT scope mismatch" };
    }
    return { scope: DEPARTMENT, allowed: true, reason: "DEPARTMENT scope" };
  }

  if (targetEmployeeId && !isOwner(user, targetEmployeeId)) {
    return { scope: EMPLOYEE, allowed: false, reason: "EMPLOYEE self scope required" };
  }
  return { scope: EMPLOYEE, allowed: true, reason: "EMPLOYEE self scope" };
};

export const canPerformAction = (
  user,
  {
    requiredPermissions = [],
    requireAllPermissions = false,
    selfScopeOnly = false,
    targetEmployeeId,
    targetDepartmentCode,
    userDepartmentCode,
  } = {},
) => {
  const permissions = resolveUserPermissions(user);
  const checks = requiredPermissions
    .map((permission) => String(permission || "").trim())
    .filter(Boolean);

  if (checks.length > 0) {
    if (requireAllPermissions) {
      if (!checks.every((permission) => permissions.has(permission))) return false;
    } else if (!checks.some((permission) => permissions.has(permission))) {
      return false;
    }
  }

  const scope = resolveScopeAccess(user, {
    targetEmployeeId,
    targetDepartmentCode,
    userDepartmentCode,
  });
  if (selfScopeOnly) return scope.scope === EMPLOYEE && scope.allowed;
  return scope.allowed;
};

export const createPermissionSelectors = ({ user, moduleAccess, activeRole }) => {
  const can = (permission) => canPerformAction(user, { requiredPermissions: [permission] });
  const canAny = (permissions = []) => permissions.some((permission) => can(permission));
  const canAll = (permissions = []) => permissions.every((permission) => can(permission));
  const canAccessModule = (moduleId) => {
    if (!moduleId) return true;
    if (moduleAccess?.mode === "allow_all") return true;
    const allowedModules = Array.isArray(moduleAccess?.allowed_modules) ? moduleAccess.allowed_modules : [];
    return allowedModules.includes(moduleId);
  };
  const getPrimaryAuthority = () => {
    if (!user?.authorities?.length) return "EMPLOYEE";
    if (activeRole && user.authorities.includes(activeRole)) return activeRole;
    for (const authority of AUTHORITY_PRIORITY) {
      if (user.authorities.includes(authority)) return authority;
    }
    return user.authorities[0];
  };

  return {
    can,
    canAny,
    canAll,
    is: (authority) => hasAuthority(user, authority),
    isAny: (authorities) => hasAnyAuthority(user, authorities),
    canVerify: () => can(Permissions.SERVICE_BOOK_ENTRY_VERIFY),
    canApprove: () => can(Permissions.SERVICE_BOOK_ENTRY_APPROVE),
    canAttest: () => can(Permissions.SERVICE_BOOK_ENTRY_ATTEST),
    canAudit: () => can(Permissions.AUDIT_READ_ALL),
    canCreateEntry: () => can(Permissions.SERVICE_BOOK_ENTRY_CREATE),
    canSupersede: () => can(Permissions.SERVICE_BOOK_SUPERSEDE),
    canCreateProfile: () => can(Permissions.PROFILE_CREATE),
    canReadAllProfiles: () => can(Permissions.PROFILE_READ_ALL),
    canUpdateProfile: () => canAny([Permissions.PROFILE_UPDATE_ALL, Permissions.PROFILE_UPDATE_OWN_LIMITED]),
    canAccessModule,
    canAccessEssPortal: () => canAccessModule("ess_portal"),
    getAccessScope: () => resolveScopeAccess(user).scope,
    getResolvedPermissions: () => Array.from(resolveUserPermissions(user)),
    getGlobalAuthorities: () => {
      if (!user?.authorities?.length) return [];
      return user.authorities.filter((authority) => authority && authority !== "EMPLOYEE");
    },
    getPrimaryAuthority,
    getAuthorityDisplayName: (authority) => AUTHORITY_DISPLAY_NAMES[authority] || authority,
    Permissions,
    Authorities,
  };
};
