import { apiClient as api } from "@/platform/api/httpClient";

export const printAPI = {
  printPart: (employeeId, partKey) => api.get(`/service-book/employees/${employeeId}/print/part/${partKey}`),
  printFull: (employeeId) => api.get(`/service-book/employees/${employeeId}/print/full`),
};

