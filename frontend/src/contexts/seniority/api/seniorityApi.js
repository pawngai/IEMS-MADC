import { apiClient as api } from "@/platform/api/httpClient";

/**
 * Seniority Management context API.
 *
 * Canonical prefix: /seniority
 */
export const seniorityAPI = {
  getServices: () => api.get('/seniority/services'),
  getDesignations: () => api.get('/seniority/designations'),
  generateList: (data) => api.post('/seniority/generate', data),
  getLists: (params) => api.get('/seniority/lists', { params }),
  getListDetail: (listId) => api.get(`/seniority/lists/${listId}`),
  overrideRanks: (listId, data) => api.put(`/seniority/lists/${listId}/ranks`, data),
  submitList: (listId, remarks) => api.post(`/seniority/lists/${listId}/submit`, { remarks }),
  verifyList: (listId, remarks) => api.post(`/seniority/lists/${listId}/verify`, { remarks }),
  approveList: (listId, remarks) => api.post(`/seniority/lists/${listId}/approve`, { remarks }),
  rejectList: (listId, remarks) => api.post(`/seniority/lists/${listId}/reject`, { remarks }),
  promoteList: (listId, remarks) => api.post(`/seniority/lists/${listId}/promote`, { remarks }),
  exportListCSV: (listId) => api.get(`/seniority/lists/${listId}/export`, { responseType: 'blob' }),
};
