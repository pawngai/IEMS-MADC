import { apiClient as api } from "@/platform/api/httpClient";

export const employeeIdentityApi = {
  getBootstrap: () => api.get("/employee-identities/bootstrap"),
  list: (params) => api.get("/employee-identities/", { params }),
  get: (employeeId) => api.get(`/employee-identities/${employeeId}`),
  create: (data) => api.post("/employee-identities/", data),
  update: (employeeId, data) => api.put(`/employee-identities/${employeeId}`, data),
};
