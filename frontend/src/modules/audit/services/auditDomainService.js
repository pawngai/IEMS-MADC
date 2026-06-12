import { apiClient as api } from "@/platform/api/httpClient";

export const recordAuditEntry = (payload) => api.post("/audit/logs", payload);

export const buildAuditTrail = (params = {}) => {
  const next = { ...params };
  if (next.resource_type === "service_book" || next.employee_id) {
    return api.get("/audit/service-book-logs", {
      params: {
        employee_id: next.employee_id,
        limit: next.limit,
      },
    });
  }
  return api.get("/audit/logs", { params: next });
};
