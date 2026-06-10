import { beforeEach, describe, expect, test, vi } from "vitest";

const mockApiGet = vi.fn();

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  apiClient: {
    get: (...args) => mockApiGet(...args),
  },
}));

import {
  analyticsAPI,
  clearAnalyticsInflightRequests,
} from "@/contexts/analytics/api/analyticsApi";

describe("analyticsAPI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAnalyticsInflightRequests();
  });

  test("dedupes concurrent overview requests", async () => {
    let resolveRequest;
    const pendingRequest = new Promise((resolve) => {
      resolveRequest = resolve;
    });
    mockApiGet.mockReturnValueOnce(pendingRequest);

    const firstRequest = analyticsAPI.getOverview();
    const secondRequest = analyticsAPI.getOverview();

    expect(mockApiGet).toHaveBeenCalledTimes(1);
    expect(firstRequest).toBe(secondRequest);

    resolveRequest({ data: { total_employees: 1 } });

    await expect(firstRequest).resolves.toEqual({ data: { total_employees: 1 } });
  });

  test("allows a new overview request after the in-flight one settles", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { total_employees: 1 } });
    mockApiGet.mockResolvedValueOnce({ data: { total_employees: 2 } });

    await analyticsAPI.getOverview();
    await analyticsAPI.getOverview();

    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });

  test("forwards analytics drilldown params", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { total: 1, rows: [] } });

    await analyticsAPI.getDrilldown({
      section: "workforce",
      dimension: "gender",
      values: ["Male", "MALE"],
      limit: 25,
    });

    expect(mockApiGet).toHaveBeenCalledWith("/reporting/analytics/drilldown", {
      params: {
        section: "workforce",
        dimension: "gender",
        values: "Male,MALE",
        limit: 25,
      },
    });
  });

  test("requests drilldown CSV as a blob", async () => {
    mockApiGet.mockResolvedValueOnce({ data: new Blob(["Employee ID\nemp-1\n"]) });

    await analyticsAPI.exportDrilldownCSV({
      section: "workflow",
      dimension: "stage",
      value: "LOCKED",
      limit: 5000,
    });

    expect(mockApiGet).toHaveBeenCalledWith("/reporting/analytics/drilldown/export", {
      params: {
        section: "workflow",
        dimension: "stage",
        value: "LOCKED",
        limit: 5000,
      },
      responseType: "blob",
    });
  });
});