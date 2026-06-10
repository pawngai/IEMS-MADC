import { describe, expect, test, vi } from "vitest";

const mockGetEmployeeCompletionStatus = vi.fn();

vi.mock("@/shared/lib/utils", () => ({
  getEmployeeCompletionStatus: (...args) => mockGetEmployeeCompletionStatus(...args),
}));

import {
  filterQueuedProfilesByStage,
  getProfileQueueStagesForAuthority,
  shouldQueueProfileItem,
} from "@/shared/lib/profileWorkflowQueue";

describe("profileWorkflowQueue", () => {
  test("maps authorities to the expected profile workflow stages", () => {
    expect(getProfileQueueStagesForAuthority("GLOBAL_DATA_ENTRY")).toEqual(["DRAFT", "REJECTED"]);
    expect(getProfileQueueStagesForAuthority("VERIFIER")).toEqual(["SUBMITTED"]);
    expect(getProfileQueueStagesForAuthority("APPROVING_AUTHORITY")).toEqual(["VERIFIED", "APPROVED"]);
    expect(getProfileQueueStagesForAuthority("DDO")).toEqual([]);
    expect(getProfileQueueStagesForAuthority("HOD")).toEqual(["APPROVED"]);
    expect(getProfileQueueStagesForAuthority("APPOINTING_AUTHORITY")).toEqual([]);
    expect(getProfileQueueStagesForAuthority("DISCIPLINARY_AUTHORITY")).toEqual([]);
    expect(getProfileQueueStagesForAuthority("AUDITOR")).toEqual([]);
  });

  test("keeps non-draft profiles in the pending workflow buckets", () => {
    mockGetEmployeeCompletionStatus.mockReturnValue({ known: true, complete: false });

    expect(shouldQueueProfileItem({ workflow_status: "REJECTED", employee_section_completed: false }, "REJECTED")).toBe(true);
    expect(shouldQueueProfileItem({ workflow_status: "SUBMITTED", employee_section_completed: false }, "SUBMITTED")).toBe(true);
  });

  test("filters profiles whose actual workflow status does not match the requested queue stage", () => {
    mockGetEmployeeCompletionStatus.mockReturnValue({ known: true, complete: true });

    const filtered = filterQueuedProfilesByStage(
      [
        {
          employee_id: "MADC-0111",
          workflow_status: "SUBMITTED",
          identity_workflow_status: "ACTIVE",
          employee_section_completed: true,
          data_entry_section_completed: true,
        },
        {
          employee_id: "EMP-DRAFT",
          workflow_status: "DRAFT",
          identity_workflow_status: "ACTIVE",
          employee_section_completed: true,
          data_entry_section_completed: false,
        },
      ],
      "DRAFT"
    );

    expect(filtered.map((profile) => profile.employee_id)).toEqual(["EMP-DRAFT"]);
  });

  test("filters untouched draft profiles out of queue-driven counters", () => {
    mockGetEmployeeCompletionStatus
      .mockReturnValueOnce({ known: true, complete: false })
      .mockReturnValueOnce({ known: true, complete: true })
      .mockReturnValueOnce({ known: true, complete: false });

    const filtered = filterQueuedProfilesByStage(
      [
        {
          employee_id: "EMP-HIDDEN",
          workflow_status: "DRAFT",
          employee_section_completed: false,
          data_entry_section_completed: false,
        },
        {
          employee_id: "EMP-EMPLOYEE-STARTED",
          workflow_status: "DRAFT",
          employee_section_completed: true,
          data_entry_section_completed: false,
        },
        {
          employee_id: "EMP-DATA-ENTRY-STARTED",
          workflow_status: "DRAFT",
          employee_section_completed: false,
          data_entry_section_completed: true,
        },
      ],
      "DRAFT"
    );

    expect(filtered.map((profile) => profile.employee_id)).toEqual([
      "EMP-EMPLOYEE-STARTED",
      "EMP-DATA-ENTRY-STARTED",
    ]);
  });

  test("filters unactivated identity projections out of draft profile queues", () => {
    mockGetEmployeeCompletionStatus.mockReturnValue({ known: true, complete: true });

    const filtered = filterQueuedProfilesByStage(
      [
        {
          employee_id: "EMP-IDENTITY-DRAFT",
          workflow_status: "DRAFT",
          identity_workflow_status: "DRAFT",
          employee_section_completed: true,
        },
        {
          employee_id: "EMP-IDENTITY-ACTIVE",
          workflow_status: "DRAFT",
          identity_workflow_status: "ACTIVE",
          employee_section_completed: true,
        },
      ],
      "DRAFT"
    );

    expect(filtered.map((profile) => profile.employee_id)).toEqual(["EMP-IDENTITY-ACTIVE"]);
  });
});
