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

const getUserDepartmentCode = (user) => {
  const code = String(user?.department_code || user?.department_id || "").trim().toUpperCase();
  return code || null;
};

const isOwner = (user, targetEmployeeId) => {
  const callerEmployeeId = String(user?.employee_id || "").trim();
  const target = String(targetEmployeeId || "").trim();
  return Boolean(callerEmployeeId && target && callerEmployeeId === target);
};

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

export const resolveUserPermissions = (user) => {
  const explicit = Array.isArray(user?.permissions)
    ? user.permissions
    : user?.permissions
      ? [user.permissions]
      : [];
  if (explicit.length > 0) {
    return new Set(explicit.map((permission) => String(permission).trim()).filter(Boolean));
  }

  return new Set();
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

  if (scope === GLOBAL) {
    return { scope: GLOBAL, allowed: true, reason: "GLOBAL scope" };
  }

  if (scope === DEPARTMENT) {
    const actorDepartment = String(userDepartmentCode || getUserDepartmentCode(user) || "").trim().toUpperCase();
    const targetDepartment = String(targetDepartmentCode || "").trim().toUpperCase();
    if (!actorDepartment) {
      return { scope: DEPARTMENT, allowed: false, reason: "DEPARTMENT scope requires caller department mapping" };
    }
    if (actorDepartment && targetDepartment && actorDepartment !== targetDepartment) {
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
  if (selfScopeOnly) {
    return scope.scope === EMPLOYEE && scope.allowed;
  }
  return scope.allowed;
};
