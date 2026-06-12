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

import { buildAuditTrail, recordAuditEntry } from "@/modules/audit/services/auditDomainService";

describe("auditDomainService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("recordAuditEntry posts to audit logs endpoint", async () => {
    mockApiPost.mockResolvedValue({ data: { ok: true } });
    await recordAuditEntry({ action: "TEST" });
    expect(mockApiPost).toHaveBeenCalledWith("/audit/logs", { action: "TEST" });
  });

  test("buildAuditTrail routes service_book queries to service-book-logs endpoint", async () => {
    mockApiGet.mockResolvedValue({ data: [] });

    await buildAuditTrail({ limit: 10 });
    await buildAuditTrail({ resource_type: "service_book", employee_id: "EMP-1", limit: 10 });

    expect(mockApiGet).toHaveBeenCalledWith("/audit/logs", { params: { limit: 10 } });
    expect(mockApiGet).toHaveBeenCalledWith("/audit/service-book-logs", {
      params: { employee_id: "EMP-1", limit: 10 },
    });
  });
});
