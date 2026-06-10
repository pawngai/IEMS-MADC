import { apiClient as api } from "@/platform/api/httpClient";

const BASE = "/service-book/opening";

export const serviceBookOpeningApi = {
  listQueue: (params = {}) => api.get(BASE, { params }),
  getForEmployee: (employeeId) => api.get(`${BASE}/${employeeId}`),
  getPartIDefaults: (employeeId) => api.get(`${BASE}/${employeeId}/part-i/defaults`),
  getEmployeeIdentity: (employeeId) => api.get(`/employee-identities/${employeeId}`),
  getEmployeeProfile: (employeeId) => api.get(`/employee-profiles/${employeeId}`),
  createDraft: (payload) => api.post(BASE, payload),
  updateDraft: (employeeId, payload) => api.patch(`${BASE}/${employeeId}`, payload),
  submit: (employeeId, remarks) => api.post(`${BASE}/${employeeId}/submit`, { remarks: remarks || undefined }),
  verify: (employeeId, remarks) => api.post(`${BASE}/${employeeId}/verify`, { remarks: remarks || undefined }),
  approve: (employeeId, remarks) => api.post(`${BASE}/${employeeId}/approve`, { remarks: remarks || undefined }),
  attachDocument: (employeeId, payload) => api.post(`${BASE}/${employeeId}/documents`, payload),
  uploadLinkedDocument: (file, metadata = {}) => {
    const params = new URLSearchParams();
    Object.entries(metadata || {}).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return;
      params.set(key, value);
    });
    const formData = new FormData();
    formData.append("file", file);
    const suffix = params.toString();
    return api.post(`/documents/document${suffix ? `?${suffix}` : ""}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export default serviceBookOpeningApi;
