import { beforeEach, describe, expect, test, vi } from "vitest";

const mockApiGet = vi.fn();
const mockApiPost = vi.fn();

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  apiClient: {
    get: (...args) => mockApiGet(...args),
    post: (...args) => mockApiPost(...args),
  },
}));

import {
  approveProfile,
  clearWorkQueueInflightRequests,
  getProfileAuditTrail,
  getProfileCompletion,
  getMyEssProfile,
  listProfilesByStatus,
  listServiceBookOpeningQueue,
  listServiceBookQueue,
  lockProfile,
  rejectProfile,
  submitServiceBookOpening,
  submitProfile,
  verifyProfile,
} from "@/contexts/workflow/model/workQueueGateway";

describe("workQueueGateway", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearWorkQueueInflightRequests();
  });

  test("getMyEssProfile returns profile payload when available", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { employee_id: "EMP-1" } });

    await expect(getMyEssProfile()).resolves.toEqual({ employee_id: "EMP-1" });
    expect(mockApiGet).toHaveBeenCalledWith("/ess/my-profile");
  });

  test("getMyEssProfile returns null on API failure", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("network"));

    await expect(getMyEssProfile()).resolves.toBeNull();
  });

  test("listProfilesByStatus forwards status with default page size", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { profiles: [{ employee_id: "EMP-2" }] } });

    await expect(listProfilesByStatus("DRAFT")).resolves.toEqual([{ employee_id: "EMP-2" }]);
    expect(mockApiGet).toHaveBeenCalledWith("/employee-profiles/", {
      params: { workflow_status: "DRAFT", page_size: 200, profile_workflow_only: true },
    });
  });

  test("listProfilesByStatus supports custom page size", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { profiles: [] } });

    await listProfilesByStatus("SUBMITTED", 50);
    expect(mockApiGet).toHaveBeenCalledWith("/employee-profiles/", {
      params: { workflow_status: "SUBMITTED", page_size: 50, profile_workflow_only: true },
    });
  });

  test("dedupes concurrent profile status requests", async () => {
    let resolveRequest;
    const pendingRequest = new Promise((resolve) => {
      resolveRequest = resolve;
    });
    mockApiGet.mockReturnValueOnce(pendingRequest);

    const firstRequest = listProfilesByStatus("DRAFT");
    const secondRequest = listProfilesByStatus("DRAFT");

    expect(mockApiGet).toHaveBeenCalledTimes(1);

    resolveRequest({ data: { profiles: [{ employee_id: "EMP-4" }] } });

    await expect(firstRequest).resolves.toEqual([{ employee_id: "EMP-4" }]);
    await expect(secondRequest).resolves.toEqual([{ employee_id: "EMP-4" }]);
  });

  test("allows a new profile status request after the previous one settles", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { profiles: [] } });
    mockApiGet.mockResolvedValueOnce({ data: { profiles: [] } });

    await listProfilesByStatus("DRAFT");
    await listProfilesByStatus("DRAFT");

    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });

  test("getProfileCompletion unwraps completion payload", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { overall_percent: 75 } });

    await expect(getProfileCompletion("EMP-9")).resolves.toEqual({ overall_percent: 75 });
    expect(mockApiGet).toHaveBeenCalledWith("/employee-profiles/EMP-9/completion");
  });

  test("getProfileAuditTrail unwraps audit trail entries", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { audit_trail: [{ id: "AUD-1" }] } });

    await expect(getProfileAuditTrail("EMP-10")).resolves.toEqual([{ id: "AUD-1" }]);
    expect(mockApiGet).toHaveBeenCalledWith("/employee-profiles/EMP-10/audit-trail");
  });

  test("listServiceBookQueue forwards multiple workflow states in one request", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { entries: [{ id: "SB-1" }] } });

    await expect(listServiceBookQueue(["DRAFT", "REJECTED"], 200)).resolves.toEqual([{ id: "SB-1" }]);
    expect(mockApiGet).toHaveBeenCalledWith("/service-book/queue", {
      params: { page_size: 200, workflow_states: "DRAFT,REJECTED" },
    });
  });

  test("listServiceBookQueue forwards a single workflow state", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { entries: [{ id: "SB-2" }] } });

    await expect(listServiceBookQueue("SUBMITTED", 200)).resolves.toEqual([{ id: "SB-2" }]);
    expect(mockApiGet).toHaveBeenCalledWith("/service-book/queue", {
      params: { page_size: 200, workflow_state: "SUBMITTED" },
    });
  });

  test("listServiceBookOpeningQueue forwards the opening workflow state", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { items: [{ employee_id: "EMP-OPEN-1" }] } });

    await expect(listServiceBookOpeningQueue("DRAFT", 200)).resolves.toEqual([{ employee_id: "EMP-OPEN-1" }]);
    expect(mockApiGet).toHaveBeenCalledWith("/service-book/opening", {
      params: { page_size: 200, workflow_state: "DRAFT" },
    });
  });

  test("profile action helpers delegate with optional remarks behavior", async () => {
    mockApiPost.mockResolvedValue({ ok: true });

    await submitProfile("EMP-1", "");
    await verifyProfile("EMP-1", "verify");
    await approveProfile("EMP-1", undefined);
    await lockProfile("EMP-1", "lock");
    await rejectProfile("EMP-1", "reject");

    expect(mockApiPost).toHaveBeenCalledWith("/employee-profiles/EMP-1/submit", { remarks: undefined });
    expect(mockApiPost).toHaveBeenCalledWith("/employee-profiles/EMP-1/verify", { remarks: "verify" });
    expect(mockApiPost).toHaveBeenCalledWith("/employee-profiles/EMP-1/approve", { remarks: undefined });
    expect(mockApiPost).toHaveBeenCalledWith("/employee-profiles/EMP-1/lock", { remarks: "lock" });
    expect(mockApiPost).toHaveBeenCalledWith("/employee-profiles/EMP-1/reject", { remarks: "reject" });
  });

  test("service book opening submit delegates with optional remarks behavior", async () => {
    mockApiPost.mockResolvedValue({ ok: true });

    await submitServiceBookOpening("EMP-OPEN-2", "");

    expect(mockApiPost).toHaveBeenCalledWith("/service-book/opening/EMP-OPEN-2/submit", { remarks: undefined });
  });

});

