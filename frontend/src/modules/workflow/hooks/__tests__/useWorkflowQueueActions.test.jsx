import { renderHook } from "@testing-library/react";

import { useWorkflowQueueActions } from "@/modules/workflow/hooks/useWorkflowQueueActions";

const profileItem = (stage) => ({
  type: "profile",
  stage,
  employeeId: "EMP-001",
  raw: {
    employee_section_completed: true,
    data_entry_section_completed: true,
  },
});

describe("useWorkflowQueueActions", () => {
  test("data entry profile draft items expose submit when both sections are complete", () => {
    const globalDataEntry = renderHook(() => useWorkflowQueueActions({ authority: "GLOBAL_DATA_ENTRY" }));

    expect(globalDataEntry.result.current.getActions(profileItem("DRAFT"))).toEqual([
      { id: "profile-submit", label: "Submit", variant: "default", requiresRemarks: false },
    ]);
    expect(globalDataEntry.result.current.getActions(profileItem("REJECTED"))).toEqual([
      { id: "profile-submit", label: "Submit", variant: "default", requiresRemarks: false },
    ]);
  });

  test("data entry profile draft items hide submit until the profile is complete", () => {
    const globalDataEntry = renderHook(() => useWorkflowQueueActions({ authority: "GLOBAL_DATA_ENTRY" }));

    expect(globalDataEntry.result.current.getActions({
      ...profileItem("DRAFT"),
      raw: {
        employee_section_completed: true,
        data_entry_section_completed: false,
      },
    })).toEqual([]);
  });

  test("data entry identity draft items expose work queue submit actions", () => {
    const globalDataEntry = renderHook(() => useWorkflowQueueActions({ authority: "GLOBAL_DATA_ENTRY" }));

    expect(globalDataEntry.result.current.getActions({ type: "identity", stage: "DRAFT", employeeId: "EMP-001" })).toEqual([
      { id: "identity-submit", label: "Submit", variant: "default", requiresRemarks: false },
    ]);
    expect(globalDataEntry.result.current.getActions({ type: "identity", stage: "REJECTED", employeeId: "EMP-001" })).toEqual([
      { id: "identity-submit", label: "Submit", variant: "default", requiresRemarks: false },
    ]);
  });

  test("only approving authority can approve verified profiles", () => {
    const approvingAuthority = renderHook(() => useWorkflowQueueActions({ authority: "APPROVING_AUTHORITY" }));
    const ddo = renderHook(() => useWorkflowQueueActions({ authority: "DDO" }));

    expect(approvingAuthority.result.current.getActions(profileItem("VERIFIED")).map((action) => action.id)).toEqual([
      "profile-approve",
      "profile-reject",
    ]);
    expect(ddo.result.current.getActions(profileItem("VERIFIED"))).toEqual([]);
  });

  test("only approving authority and HOD can lock approved profiles", () => {
    const approvingAuthority = renderHook(() => useWorkflowQueueActions({ authority: "APPROVING_AUTHORITY" }));
    const hod = renderHook(() => useWorkflowQueueActions({ authority: "HOD" }));
    const appointingAuthority = renderHook(() => useWorkflowQueueActions({ authority: "APPOINTING_AUTHORITY" }));
    const disciplinaryAuthority = renderHook(() => useWorkflowQueueActions({ authority: "DISCIPLINARY_AUTHORITY" }));

    expect(approvingAuthority.result.current.getActions(profileItem("APPROVED")).map((action) => action.id)).toEqual([
      "profile-lock",
    ]);
    expect(hod.result.current.getActions(profileItem("APPROVED")).map((action) => action.id)).toEqual([
      "profile-lock",
    ]);
    expect(appointingAuthority.result.current.getActions(profileItem("APPROVED"))).toEqual([]);
    expect(disciplinaryAuthority.result.current.getActions(profileItem("APPROVED"))).toEqual([]);
  });

  test("non-regular service records are not workflow queue action items", () => {
    const verifier = renderHook(() => useWorkflowQueueActions({ authority: "VERIFIER" }));

    expect(verifier.result.current.getActions({ type: "service_record", stage: "SUBMITTED", raw: { service_event_id: "SR-1" } })).toEqual([]);
  });
});
