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
  applyLeaveRequest,
  approveLeave,
  updateLeaveBalance,
} from "@/contexts/leave/services/leaveDomainService";

describe("leaveDomainService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("applies leave and updates balance routes", async () => {
    mockApiPost.mockResolvedValue({ data: { ok: true } });
    mockApiGet.mockResolvedValue({ data: { available: 10 } });

    await applyLeaveRequest({ employee_id: "EMP-1" });
    await approveLeave("LEAVE-1", {
      remarks: "ok",
      order_number: "ORD-1",
      order_date: "2026-03-16",
    });
    await updateLeaveBalance("EMP-1");

    expect(mockApiPost).toHaveBeenCalledWith("/leave/apply", { employee_id: "EMP-1" });
    expect(mockApiPost).toHaveBeenCalledWith("/leave/LEAVE-1/sanction", {
      remarks: "ok",
      order_number: "ORD-1",
      order_date: "2026-03-16",
    });
    expect(mockApiGet).toHaveBeenCalledWith("/leave/balances/EMP-1");
  });

  test("keeps backward compatibility for remarks-only sanction calls", async () => {
    mockApiPost.mockResolvedValue({ data: { ok: true } });

    await approveLeave("LEAVE-2", "legacy remarks");

    expect(mockApiPost).toHaveBeenCalledWith("/leave/LEAVE-2/sanction", {
      remarks: "legacy remarks",
      order_number: undefined,
      order_date: undefined,
    });
  });
});
