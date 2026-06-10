export const payApi = {
  revisions: (api, payload) => api.post("/pay/revisions", payload),
  allowances: (api, payload) => api.post("/pay/allowances", payload),
  ledger: (api, employeeId) => api.get(`/pay/ledger/${employeeId}`),
  snapshot: (api, employeeId) => api.get(`/pay/snapshot/${employeeId}`),
};
