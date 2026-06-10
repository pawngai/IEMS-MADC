import { describe, expect, test } from "vitest";

import { enrichAndSortQueueItems, toIdentityItems, toProfileItems, toServiceBookItems, toServiceBookOpeningItems } from "@/contexts/workflow/model/workflowQueueMapper";

describe("workflowQueueMapper", () => {
  test("normalizes synthetic seeded profile names for queue display", () => {
    const [item] = toProfileItems({
      stage: "DRAFT",
      profiles: [
        {
          employee_id: "EMP-9",
          employee_code: "MADC-2024-0009",
          full_name: "TEST_WORKFLOW_564dc21b",
          workflow_status: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.title).toBe("Test Workflow");
    expect(item.subtitle).toBe("MADC-2024-0009");
    expect(item.displayName).toBe("Test Workflow");
  });

  test("uses the profile workflow status as the actionable queue stage", () => {
    const [item] = toProfileItems({
      stage: "DRAFT",
      profiles: [
        {
          employee_id: "EMP-10",
          employee_code: "MADC-0111",
          full_name: "Submitted Profile",
          workflow_status: "SUBMITTED",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.stage).toBe("SUBMITTED");
    expect(item.statusLabel).toBe("SUBMITTED");
  });

  test("maps identity queue items with readable labels", () => {
    const [item] = toIdentityItems({
      stage: "SUBMITTED",
      identities: [
        {
          employee_id: "EMP-55",
          employee_code: "MADC-2024-R0055",
          full_name: "TEST_IDENTITY_QUEUE_4c0f2a",
          current_department_id: "FIN",
          current_designation_id: "LDC",
          workflow_status: "SUBMITTED",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.type).toBe("identity");
    expect(item.title).toBe("Test Identity Queue");
    expect(item.subtitle).toBe("MADC-2024-R0055 • FIN • LDC");
  });

  test("humanizes service-book queue labels from raw part and schema keys", () => {
    const [item] = toServiceBookItems({
      stage: "DRAFT",
      entries: [
        {
          id: "90c487",
          employee_id: "EMP-1",
          employee_code: "MADC-2024-0001",
          full_name: "Sample Employee",
          part_key: "III",
          schema_key: "SB_PART_III_FOREIGN_SERVICE_ROW",
          workflow_state: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.title).toBe("Sample Employee");
    expect(item.subtitle).toBe("MADC-2024-0001 • Part III: Previous Service • Foreign Service");
  });

  test("uses schema and part labels when employee identity is unavailable", () => {
    const [item] = toServiceBookItems({
      stage: "DRAFT",
      entries: [
        {
          id: "7feb9d",
          employee_id: "EMP-2",
          part_key: "III",
          schema_key: "SB_III_FOREIGN_SERVICE_ROW",
          workflow_state: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.title).toBe("EMP-2");
    expect(item.subtitle).toBe("Part III: Previous Service • Foreign Service");
    expect(item.displayName).toBeNull();
  });

  test("shortens opaque employee and entry identifiers for sparse service-book items", () => {
    const [item] = toServiceBookItems({
      stage: "DRAFT",
      entries: [
        {
          id: "90c48712-1234-4567-89ab-abcdef123456",
          employee_id: "f1c9a4cc-f7e6-4a7a-9c60-2802296dbb5d",
          part_key: "III",
          schema_key: "SB_III_FOREIGN_SERVICE_ROW",
          workflow_state: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.title).toBe("Employee f1c9a4cc");
    expect(item.subtitle).toBe("Part III: Previous Service • Foreign Service • Entry 90c48712");
  });

  test("normalizes part II-A and II-B schema prefixes without leaking roman-code fragments", () => {
    const [immutableItem, mutableItem] = toServiceBookItems({
      stage: "DRAFT",
      entries: [
        {
          id: "iia-1",
          employee_id: "EMP-20",
          employee_code: "MADC-2020-0001",
          full_name: "Rahul Sharma",
          part_key: "II-A",
          schema_key: "SB_PART_IIA_IMMUTABLE_CERTS_ROW",
          workflow_state: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
        {
          id: "iib-1",
          employee_id: "EMP-20",
          employee_code: "MADC-2020-0001",
          full_name: "Rahul Sharma",
          part_key: "II-B",
          schema_key: "SB_PART_IIB_PCF_NOMINATION_ROW",
          workflow_state: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(immutableItem.subtitle).toBe("MADC-2020-0001 • Part II-A: Immutable Certs");
    expect(mutableItem.subtitle).toBe("MADC-2020-0001 • Part II-B: Mutable Certs • Pcf Nomination");
  });

  test("maps service book opening queue items with readable employee labels", () => {
    const [item] = toServiceBookOpeningItems({
      stage: "DRAFT",
      openings: [
        {
          employee_id: "EMP-OPEN-5",
          employee_code: "MADC-OPEN-0005",
          full_name: "Opening Employee",
          workflow_status: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });

    expect(item.type).toBe("service_opening");
    expect(item.title).toBe("Opening Employee");
    expect(item.subtitle).toBe("MADC-OPEN-0005 • Opening Workflow");
  });

  test("disambiguates profile and identity queue items for the same employee and stage", () => {
    const [profileItem] = toProfileItems({
      stage: "DRAFT",
      profiles: [
        {
          employee_id: "EMP-42",
          employee_code: "MADC-2024-0042",
          full_name: "Asha Queue",
          workflow_status: "DRAFT",
          updated_at: "2026-04-06T00:00:00Z",
        },
      ],
    });
    const [identityItem] = toIdentityItems({
      stage: "DRAFT",
      identities: [
        {
          employee_id: "EMP-42",
          employee_code: "MADC-2024-0042",
          full_name: "Asha Queue",
          workflow_status: "DRAFT",
          updated_at: "2026-04-07T00:00:00Z",
        },
      ],
    });

    const items = enrichAndSortQueueItems([profileItem, identityItem]);
    const byType = new Map(items.map((item) => [item.type, item]));

    expect(byType.get("identity")?.subtitle).toContain("Identity workflow");
    expect(byType.get("profile")?.subtitle).toContain("Profile workflow");
  });
});
