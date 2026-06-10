import { apiClient as api } from "@/platform/api/httpClient";

export const serviceRecordsApi = {
  create: (payload) => api.post("/service-book/service-records", payload),
  submit: (recordId) => api.post(`/service-book/service-records/${recordId}/submit`),
  verify: (recordId) => api.post(`/service-book/service-records/${recordId}/verify`),
  approve: (recordId) => api.post(`/service-book/service-records/${recordId}/approve`),
  post: (recordId) => api.post(`/service-book/service-records/${recordId}/post`),
  listByEmployee: (employeeId) => api.get(`/service-book/service-records/employees/${employeeId}`),
  getServiceSummary: (employeeId) => api.get(`/service-book/employee-service-summaries/${employeeId}`),
};
