import { apiClient as api } from "@/platform/api/httpClient";

export const computePayRecord = (employeeId) =>
  api.get(`/pay/snapshot/${employeeId}`);

export const applyPayChange = (payload) => {
  if (payload?.allowance_code) {
    return api.post("/pay/allowances", payload);
  }
  return api.post("/pay/revisions", payload);
};
