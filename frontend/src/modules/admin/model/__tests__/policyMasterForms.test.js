import { describe, expect, test } from "vitest";

import {
  buildMasterMetadata,
  createEmptyMasterMetadata,
  getPolicyMasterCreateFields,
  validateMasterMetadata,
} from "@/modules/admin/model/policyMasterForms";

describe("policyMasterForms", () => {
  test("builds nested employment type rules metadata from the master code", () => {
    const form = createEmptyMasterMetadata("employment_type");
    form.has_pension = false;

    expect(buildMasterMetadata("employment_type", form, "REG")).toEqual({
      type_code: "REG",
      rules: {
        has_pension: false,
        has_gpf: true,
        has_leave_account: true,
        has_increment: true,
        can_be_promoted: true,
        can_be_transferred: true,
      },
    });
  });

  test("hides redundant metadata code fields in create forms", () => {
    expect(getPolicyMasterCreateFields("employment_type").map((field) => field.key)).not.toContain("type_code");
    expect(getPolicyMasterCreateFields("leave_type").map((field) => field.key)).not.toContain("leave_code");
    expect(getPolicyMasterCreateFields("caste_category").map((field) => field.key)).not.toContain("category_code");
  });

  test("requires related master selections for designation metadata", () => {
    expect(
      validateMasterMetadata("designation", {
        pay_level_code: "",
        service_group_code: "",
      }),
    ).toBe("Pay Level and Service Group are required");
  });

  test("validates numeric master constraints", () => {
    expect(
      validateMasterMetadata("pay_level", {
        pay_band: "PB-2",
        basic_min: 50000,
        basic_max: 40000,
        annual_increment_rate: 3,
      }),
    ).toBe("Basic Max must be greater than or equal to Basic Min");

    expect(
      validateMasterMetadata("caste_category", {
        reservation_percentage: 120,
      }),
    ).toBe("Reservation Percentage must be between 0 and 100");

    expect(
      validateMasterMetadata("leave_type", {
        min_days_per_spell: 5,
        max_days_per_spell: 3,
      }),
    ).toBe("Max Days Per Spell must be greater than or equal to Min Days Per Spell");
  });

  test("deduplicates role permissions", () => {
    expect(
      buildMasterMetadata("role", {
        permissions: ["MASTER_READ", "MASTER_READ", "SYSTEM_CONFIG"],
      }),
    ).toEqual({
      permissions: ["MASTER_READ", "SYSTEM_CONFIG"],
    });
  });

  test("builds workflow stage arrays without dropping empty values", () => {
    expect(
      buildMasterMetadata("workflow_stage", {
        next_stages: ["APPROVED", "REJECTED"],
        required_authority: ["APPROVING_AUTHORITY"],
        can_edit: false,
      }),
    ).toEqual({
      next_stages: ["APPROVED", "REJECTED"],
      required_authority: ["APPROVING_AUTHORITY"],
      can_edit: false,
    });
  });

  test("prevents self-referential department and workflow links", () => {
    expect(
      validateMasterMetadata(
        "department",
        {
          parent_department_code: "FIN",
        },
        "FIN",
      ),
    ).toBe("Parent Department cannot be the same as the record code");

    expect(
      validateMasterMetadata(
        "workflow_stage",
        {
          next_stages: ["APPROVED", "REJECTED"],
        },
        "APPROVED",
      ),
    ).toBe("Next Stages cannot include the current record code");
  });

  test("keeps department master metadata limited to parent department linkage", () => {
    expect(getPolicyMasterCreateFields("department")).toMatchObject([
      {
        key: "parent_department_code",
        label: "Parent Department (Optional)",
        helperText: "Department masters now only capture an optional parent department link.",
      },
    ]);

    expect(
      buildMasterMetadata(
        "department",
        {
          parent_department_code: "gad",
          ministry_code: "legacy",
          department_type: "directorate",
        },
        "FIN",
      ),
    ).toEqual({
      parent_department_code: "GAD",
    });
  });

  test("builds leave policy metadata for spell and lifetime caps", () => {
    expect(
      buildMasterMetadata("leave_type", {
        max_days_per_year: "730",
        min_days_per_spell: "5",
        max_days_per_spell: "15",
        max_days_lifetime: "730",
        is_encashable: false,
        is_accumulative: false,
        applicable_employment_types: ["reg", "dep"],
      }, "CCL"),
    ).toEqual({
      leave_code: "CCL",
      max_days_per_year: 730,
      min_days_per_spell: 5,
      max_days_per_spell: 15,
      max_days_lifetime: 730,
      is_encashable: false,
      is_accumulative: false,
      applicable_employment_types: ["REG", "DEP"],
    });
  });
});