import { ADMIN, DEPT, ESS, OPS } from "@/shared/lib/routes";
import { getDefaultLandingPath } from "@/contexts/identity_access/model/portalAccessRules";

describe("getDefaultLandingPath", () => {
  test("routes system admins to the admin console", () => {
    const path = getDefaultLandingPath({
      user: { authorities: ["SYSTEM_ADMIN"] },
      can: (permission) => ["USER_MANAGEMENT", "SYSTEM_CONFIG"].includes(permission),
      canAny: () => false,
      canAccessModule: (moduleId) => moduleId === "admin_console",
      canAccessEssPortal: () => false,
      getPrimaryAuthority: () => "SYSTEM_ADMIN",
    });

    expect(path).toBe(ADMIN.HOME);
  });

  test("routes employee-only users to ESS", () => {
    const path = getDefaultLandingPath({
      user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" },
      can: (permission) => ["PROFILE_READ_OWN", "SERVICE_BOOK_READ_OWN"].includes(permission),
      canAny: (permissions) => permissions.includes("PROFILE_READ_OWN"),
      canAccessModule: () => true,
      canAccessEssPortal: () => true,
      getPrimaryAuthority: () => "EMPLOYEE",
    });

    expect(path).toBe(ESS.DASHBOARD);
  });

  test("routes departmental roles to the departmental dashboard", () => {
    const path = getDefaultLandingPath({
      user: { authorities: ["DEPT_DATA_ENTRY"] },
      can: (permission) => permission === "PROFILE_READ_ALL",
      canAny: () => false,
      canAccessModule: () => true,
      canAccessEssPortal: () => false,
      getPrimaryAuthority: () => "DEPT_DATA_ENTRY",
    });

    expect(path).toBe(DEPT.DASHBOARD);
  });

  test("routes global data entry to the operations directory", () => {
    const path = getDefaultLandingPath({
      user: { authorities: ["GLOBAL_DATA_ENTRY"] },
      can: () => false,
      canAny: (permissions) => permissions.includes("PROFILE_READ_ALL"),
      canAccessModule: () => true,
      canAccessEssPortal: () => false,
      getPrimaryAuthority: () => "GLOBAL_DATA_ENTRY",
    });

    expect(path).toBe(OPS.EMPLOYEES);
  });

  test("routes dealing assistant like global data entry", () => {
    const path = getDefaultLandingPath({
      user: { authorities: ["DEALING_ASSISTANT"] },
      can: () => false,
      canAny: (permissions) => permissions.includes("PROFILE_READ_ALL"),
      canAccessModule: () => true,
      canAccessEssPortal: () => false,
      getPrimaryAuthority: () => "DEALING_ASSISTANT",
    });

    expect(path).toBe(OPS.EMPLOYEES);
  });

  test("routes verifier roles to the work queue", () => {
    const path = getDefaultLandingPath({
      user: { authorities: ["VERIFIER"] },
      can: () => false,
      canAny: () => false,
      canAccessModule: () => true,
      canAccessEssPortal: () => false,
      getPrimaryAuthority: () => "VERIFIER",
    });

    expect(path).toBe(OPS.WORK_QUEUE);
  });
});