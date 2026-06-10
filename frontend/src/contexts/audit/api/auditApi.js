import { apiClient as api } from "@/platform/api/httpClient";
import { buildAuditTrail, recordAuditEntry } from "@/contexts/audit/services/auditDomainService";

export const auditAPI = {
  getLogs: (params) => buildAuditTrail(params),
  getServiceBookLogs: (employeeId) =>
    buildAuditTrail({ resource_type: "service_book", employee_id: employeeId }),
  recordAuditEntry,
};

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
};
