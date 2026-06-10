import { describe, expect, test } from "vitest";

import {
  ESS_DOCUMENTS_REQUIRED_PERMISSIONS,
  assertEssPortalSession,
  assertEssSelfScope,
  canAccessEssDocuments,
  canShowEssServiceBook,
  hasEssEmployeeIdentity,
} from "@/contexts/ess/services/essDomainService";

describe("essDomainService", () => {
  test("hasEssEmployeeIdentity requires employee authority and employee id", () => {
    expect(hasEssEmployeeIdentity({ authorities: ["EMPLOYEE"], employee_id: "EMP-1" })).toBe(true);
    expect(hasEssEmployeeIdentity({ authorities: ["SYSTEM_ADMIN"], employee_id: "EMP-1" })).toBe(false);
    expect(hasEssEmployeeIdentity({ authorities: ["EMPLOYEE"], employee_id: "" })).toBe(false);
  });

  test("assertEssPortalSession blocks users without a linked employee account", () => {
    expect(assertEssPortalSession({ user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" } })).toBe(true);
    expect(() =>
      assertEssPortalSession({ user: { authorities: ["SYSTEM_ADMIN"], employee_id: "" } }),
    ).toThrow(/linked employee account/i);
  });

  test("assertEssSelfScope allows self and blocks cross-employee actions", () => {
    expect(assertEssSelfScope({ user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" }, targetEmployeeId: "EMP-1" })).toBe(true);
    expect(() =>
      assertEssSelfScope({ user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" }, targetEmployeeId: "EMP-2" }),
    ).toThrow(/self scope/i);
  });

  test("canShowEssServiceBook only for eligible self profile", () => {
    expect(
      canShowEssServiceBook({
        user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" },
        profile: { employee_id: "EMP-1", employment_type: "REGULAR" },
      }),
    ).toBe(true);

    expect(
      canShowEssServiceBook({
        user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" },
        profile: { employee_id: "EMP-1", employment_type: "CONTRACTUAL" },
      }),
    ).toBe(false);
  });

  test("canAccessEssDocuments requires ESS identity and the shared permission list", () => {
    expect(ESS_DOCUMENTS_REQUIRED_PERMISSIONS).toEqual(["DOCUMENT_READ_OWN"]);
    expect(
      canAccessEssDocuments({
        user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" },
        can: (permission) => permission === "DOCUMENT_READ_OWN",
      }),
    ).toBe(true);
    expect(
      canAccessEssDocuments({
        user: { authorities: ["EMPLOYEE"], employee_id: "EMP-1" },
        can: () => false,
      }),
    ).toBe(false);
    expect(
      canAccessEssDocuments({
        user: { authorities: ["SYSTEM_ADMIN"], employee_id: "EMP-1" },
        can: () => true,
      }),
    ).toBe(false);
  });
});
