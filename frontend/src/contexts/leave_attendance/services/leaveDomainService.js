import { apiClient as api } from "@/platform/api/httpClient";

export const applyLeaveRequest = (data) => api.post("/leave/apply", data);

export const approveLeave = (leaveId, action = {}) => {
  const payload = typeof action === "string" ? { remarks: action } : (action || {});

  return api.post(`/leave/${leaveId}/sanction`, {
    remarks: payload.remarks || undefined,
    order_number: payload.order_number || undefined,
    order_date: payload.order_date || undefined,
  });
};

export const updateLeaveBalance = (employeeId) =>
  api.get(`/leave/balances/${employeeId}`);
