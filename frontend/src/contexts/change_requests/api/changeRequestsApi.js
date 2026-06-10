import { apiClient as api } from "@/platform/api/httpClient";

export const changeRequestAPI = {
  list: (params) => api.get('/change-requests', { params }),
  get: (id) => api.get(`/change-requests/${id}`),
  review: (id, data) => api.post(`/change-requests/${id}/review`, data),
  getPendingCount: () => api.get('/change-requests/pending-count'),
};
