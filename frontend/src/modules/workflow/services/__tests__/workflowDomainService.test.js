import { beforeEach, describe, expect, test, vi } from "vitest";

const mockApiPost = vi.fn();

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  apiClient: {
    post: (...args) => mockApiPost(...args),
  },
}));

import {
  approveWorkflowItem,
  rejectWorkflowItem,
  submitWorkflowAction,
  transitionWorkflowState,
} from "@/modules/workflow/services/workflowDomainService";

describe("workflowDomainService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("transitionWorkflowState posts workflow transition action", async () => {
    mockApiPost.mockResolvedValueOnce({ data: { ok: true } });

    await transitionWorkflowState({
      taskId: "T-1",
      action: "start_review",
      remarks: "ready",
    });

    expect(mockApiPost).toHaveBeenCalledWith("/api/workflow/tasks/T-1/transition", {
      action: "START_REVIEW",
      remarks: "ready",
    });
  });

  test("submit/approve/reject map to canonical workflow transition actions", async () => {
    mockApiPost.mockResolvedValue({ data: { ok: true } });

    await submitWorkflowAction({ taskId: "T-1" });
    await approveWorkflowItem({ taskId: "T-2" });
    await rejectWorkflowItem({ taskId: "T-3", remarks: "not valid" });

    expect(mockApiPost).toHaveBeenCalledWith("/api/workflow/tasks/T-1/transition", {
      action: "START_REVIEW",
      remarks: undefined,
    });
    expect(mockApiPost).toHaveBeenCalledWith("/api/workflow/tasks/T-2/transition", {
      action: "COMPLETE",
      remarks: undefined,
    });
    expect(mockApiPost).toHaveBeenCalledWith("/api/workflow/tasks/T-3/transition", {
      action: "REJECT",
      remarks: "not valid",
    });
  });
});
