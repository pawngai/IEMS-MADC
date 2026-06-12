import { apiClient as api } from "@/platform/api/httpClient";
import {
  applyLeaveRequest,
  approveLeave,
  updateLeaveBalance,
} from "@/modules/leave_attendance/services/leaveDomainService";

export const leaveAPI = {
  apply: (data) => applyLeaveRequest(data),
  listMy: () => api.get('/leave/my'),
  cancel: (leaveId, remarks) => api.post(`/leave/${leaveId}/cancel`, { remarks }),
  getBalances: (employeeId) => updateLeaveBalance(employeeId),
  list: (params = {}) => api.get('/leave', { params }),
  getPendingActions: async (params = {}) => {
    const { statuses, status, ...rest } = params;
    const requestedStatuses = Array.isArray(statuses)
      ? statuses
      : (status ? [status] : ['SUBMITTED', 'RECOMMENDED']);
    const uniqueStatuses = [...new Set(requestedStatuses.filter(Boolean))];

    if (uniqueStatuses.length === 0) {
      return { data: [] };
    }

    const responses = await Promise.all(
      uniqueStatuses.map((pendingStatus) => api.get('/leave', { params: { ...rest, status: pendingStatus } }))
    );

    return {
      data: responses.flatMap((response) => (Array.isArray(response.data) ? response.data : [])),
    };
  },
  recommend: (leaveId, remarks) => api.post(`/leave/${leaveId}/recommend`, { remarks }),
  sanction: (leaveId, data = {}) => approveLeave(leaveId, data),
  reject: (leaveId, remarks) => api.post(`/leave/${leaveId}/reject`, { remarks }),
};
