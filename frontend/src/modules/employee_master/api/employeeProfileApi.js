import { apiClient as api, API_URL } from "@/platform/api/httpClient";

export const employeeProfileApi = {
  uploadPhoto: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/documents/photo", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  uploadSignature: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/documents/signature", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getPhotoUrl: (filename) => `${API_URL}/documents/photos/${filename}`,
  getSignatureUrl: (filename) => `${API_URL}/documents/signatures/${filename}`,
  list: (params) => api.get("/employee-profiles/", { params }),
  get: (employeeId) => api.get(`/employee-profiles/${employeeId}`),
  update: (employeeId, data) => api.put(`/employee-profiles/${employeeId}`, data),
  delete: (employeeId) => api.delete(`/employee-profiles/${employeeId}`),
  submit: (employeeId, remarks) => api.post(`/employee-profiles/${employeeId}/submit`, { remarks }),
  verify: (employeeId, remarks) => api.post(`/employee-profiles/${employeeId}/verify`, { remarks }),
  approve: (employeeId, remarks) => api.post(`/employee-profiles/${employeeId}/approve`, { remarks }),
  lock: (employeeId, remarks) => api.post(`/employee-profiles/${employeeId}/lock`, { remarks }),
  reject: (employeeId, remarks) => api.post(`/employee-profiles/${employeeId}/reject`, { remarks }),
  getAuditTrail: (employeeId) => api.get(`/employee-profiles/${employeeId}/audit-trail`),
  getCompletion: (employeeId) => api.get(`/employee-profiles/${employeeId}/completion`),
  getBulkCompletion: () => api.get("/employee-profiles/completion/bulk"),
};
