import { describe, expect, test } from "vitest";

import {
  DEPARTMENT,
  GLOBAL,
  canPerformAction,
  hasAuthority,
  isDepartmentScopedRole,
  resolveScopeAccess,
} from "@/contexts/access_control/services/authorizationService";

describe("authorizationService", () => {
  test("keeps approving authority distinct from HOD", () => {
    const user = {
      authorities: ["APPROVING_AUTHORITY"],
      permissions: ["PROFILE_READ_ALL"],
      department_code: null,
    };

    expect(hasAuthority(user, "HOD")).toBe(false);
    expect(resolveScopeAccess(user)).toEqual({
      scope: GLOBAL,
      allowed: true,
      reason: "GLOBAL scope",
    });
    expect(
      canPerformAction(user, {
        requiredPermissions: ["PROFILE_READ_ALL"],
      }),
    ).toBe(true);
  });

  test("still treats actual HOD users as department-scoped", () => {
    const user = {
      authorities: ["HOD"],
      permissions: ["PROFILE_READ_ALL"],
      department_code: null,
    };

    expect(resolveScopeAccess(user)).toEqual({
      scope: DEPARTMENT,
      allowed: false,
      reason: "DEPARTMENT scope requires caller department mapping",
    });
    expect(isDepartmentScopedRole("HOD")).toBe(true);
  });
});