import { apiClient as api } from "@/platform/api/httpClient";

export const notificationsAPI = {
  list: (params = {}) => api.get('/notifications', { params }),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
};
