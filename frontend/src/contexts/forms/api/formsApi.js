import { apiClient as api } from "@/platform/api/httpClient";

export const formsAPI = {
  getEmployeeProfileForm: (params = {}) => api.get("/forms/employee-profile", { params }),
  resolveEmployeeProfileForm: (payload) => api.post("/forms/employee-profile/resolve", payload),
  validateEmployeeProfileForm: (payload) => api.post("/forms/employee-profile/validate", payload),
  getEmployeeProfileFieldConfig: (fieldId, params = {}) =>
    api.get(`/forms/employee-profile/field/${fieldId}`, { params }),
  getEmployeeProfileParts: (params = {}) => api.get("/forms/employee-profile/parts", { params }),
  getEmployeeProfileEmploymentTypes: () => api.get("/forms/employee-profile/employment-types"),
  getEmployeeProfileReadonlyMatrix: () => api.get("/forms/employee-profile/readonly-matrix"),
};
