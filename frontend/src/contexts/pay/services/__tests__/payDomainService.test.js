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

import { applyPayChange, computePayRecord } from "@/contexts/pay/services/payDomainService";

describe("payDomainService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("computes pay record from snapshot endpoint", async () => {
    mockApiGet.mockResolvedValue({ data: { basic_pay: 50000 } });
    await computePayRecord("EMP-1");
    expect(mockApiGet).toHaveBeenCalledWith("/pay/snapshot/EMP-1");
  });

  test("routes pay change by payload type", async () => {
    mockApiPost.mockResolvedValue({ data: { ok: true } });

    await applyPayChange({ employee_id: "EMP-1", effective_date: "2026-03-10", basic_pay: 51000 });
    await applyPayChange({ employee_id: "EMP-1", effective_date: "2026-03-10", allowance_code: "DA", amount: 500 });

    expect(mockApiPost).toHaveBeenCalledWith("/pay/revisions", {
      employee_id: "EMP-1",
      effective_date: "2026-03-10",
      basic_pay: 51000,
    });
    expect(mockApiPost).toHaveBeenCalledWith("/pay/allowances", {
      employee_id: "EMP-1",
      effective_date: "2026-03-10",
      allowance_code: "DA",
      amount: 500,
    });
  });
});
