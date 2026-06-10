import { apiClient as api } from "@/platform/api/httpClient";

const analyticsInflightRequests = new Map();

const dedupeAnalyticsGet = (key, path) => {
  const existing = analyticsInflightRequests.get(key);
  if (existing) return existing;

  const pending = api.get(path).finally(() => {
    if (analyticsInflightRequests.get(key) === pending) {
      analyticsInflightRequests.delete(key);
    }
  });

  analyticsInflightRequests.set(key, pending);
  return pending;
};

export const clearAnalyticsInflightRequests = () => {
  analyticsInflightRequests.clear();
};

export const analyticsAPI = {
  getOverview:       () => dedupeAnalyticsGet("overview", "/reporting/analytics/overview"),
  getWorkforce:      () => dedupeAnalyticsGet("workforce", "/reporting/analytics/workforce"),
  getLeave:          () => dedupeAnalyticsGet("leave", "/reporting/analytics/leave-summary"),
  getWorkflow:       () => dedupeAnalyticsGet("workflow", "/reporting/analytics/workflow"),
  getServiceEvents:  () => dedupeAnalyticsGet("serviceEvents", "/reporting/analytics/service-events"),
  getDrilldown: ({ section, dimension = "all", value, values, limit = 50 }) => {
    const params = { section, dimension, limit };
    if (value != null && String(value).trim()) params.value = value;
    if (Array.isArray(values) && values.length > 0) params.values = values.join(",");
    return api.get("/reporting/analytics/drilldown", { params });
  },
  exportDrilldownCSV: ({ section, dimension = "all", value, values, limit = 5000 }) => {
    const params = { section, dimension, limit };
    if (value != null && String(value).trim()) params.value = value;
    if (Array.isArray(values) && values.length > 0) params.values = values.join(",");
    return api.get("/reporting/analytics/drilldown/export", { params, responseType: "blob" });
  },
};
