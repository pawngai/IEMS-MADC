import { apiClient as api } from "@/platform/api/httpClient";

export const departmentPortalAPI = {
  getDashboard: () => api.get('/department/dashboard'),
  getEmployees: (params) => api.get('/department/employees', { params }),
  getEmployeeSnapshot: (employeeId) => api.get(`/department/employees/${employeeId}`),
  getPendingLeaves: () => api.get('/department/pending-leaves'),
  getWorkflowOverview: (params) => api.get('/department/workflow', { params }),
  getActivity: (params) => api.get('/department/activity', { params }),
  getPendingWork: () => api.get('/department/pending-work'),
  getSanctionedStrength: () => api.get('/department/sanctioned-strength'),
  updateSanctionedStrength: (payload) => api.put('/department/sanctioned-strength', payload),
};
