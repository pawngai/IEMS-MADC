import { apiClient as api } from "@/platform/api/httpClient";

export const userManagementAPI = {
  list: (params) => api.get('/users/', { params }),
  getEmployees: (params) => api.get('/users/employees', { params }),
  count: (params) => api.get('/users/count', { params }),
  get: (userId) => api.get(`/users/${userId}`),
  create: (data) => api.post('/users/', data),
  provisionEmployeeAccount: (data) => api.post('/users/employee-accounts', data),
  update: (userId, data) => api.put(`/users/${userId}`, data),
  patchAuthorities: (userId, { add, remove, department_code } = {}) =>
    api.patch(`/users/${userId}/authorities`, { add, remove, department_code }),
  updatePassword: (userId, newPassword) => api.put(`/users/${userId}/password`, { new_password: newPassword }),
  delete: (userId) => api.delete(`/users/${userId}`),
  getAuthorities: () => api.get('/users/authorities/list'),
  getAuthorityHolders: () => api.get('/users/authorities/holders'),
  getActivityLogs: (params) => api.get('/users/activity/logs', { params }),
  getActivityStats: () => api.get('/users/activity/stats'),
  getRoleChangeHistory: (params) => api.get('/users/role-changes/history', { params }),
  getRoleChangeStats: () => api.get('/users/role-changes/stats'),
};
