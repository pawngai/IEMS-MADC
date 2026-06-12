import { apiClient as api } from "@/platform/api/httpClient";

const normalizeFilename = (filename) => encodeURIComponent(String(filename || "").trim());

export const essAPI = {
  getDashboard: () => api.get("/ess/dashboard"),
  getMyProfile: () => api.get("/ess/my-profile"),
  getMyDocuments: (params = {}) => api.get("/ess/my-documents", { params }),
  previewMyDocument: (filename) => api.get(`/ess/my-documents/${normalizeFilename(filename)}`, { responseType: "blob" }),
  downloadMyDocument: (filename) => api.get(`/ess/my-documents/${normalizeFilename(filename)}/download`, { responseType: "blob" }),
  getMyDocumentFileUrl: (filename) => `/api/ess/my-documents/${normalizeFilename(filename)}`,
  getMyDocumentDownloadUrl: (filename) => `/api/ess/my-documents/${normalizeFilename(filename)}/download`,
  getMyLeaveBalances: () => api.get("/ess/my-leave-balances"),
  updateMyContact: (data) => api.put("/ess/my-profile/contact", data),
  getMyServiceBook: () => api.get("/ess/my-service-book"),
  getMyLeaves: () => api.get("/ess/my-leaves"),
  getNotifications: () => api.get("/ess/notifications"),
  markNotificationRead: (id) => api.post(`/ess/notifications/${id}/read`),
  submitChangeRequest: (data) => api.post("/ess/change-requests", data),
  listMyChangeRequests: (params) => api.get("/ess/change-requests", { params }),
  getMyChangeRequest: (id) => api.get(`/ess/change-requests/${id}`),
  cancelChangeRequest: (id) => api.post(`/ess/change-requests/${id}/cancel`),
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/documents/document", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
