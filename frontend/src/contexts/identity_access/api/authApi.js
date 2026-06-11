import { apiClient as api } from "@/platform/api/httpClient";

export const authAPI = {
  login: (credentials) => api.post("/auth/login", credentials),
  getMe: () => api.get("/auth/me", { timeout: 2500, iemsNoRetry: true }),
  getRBACMatrix: () => api.get("/auth/rbac-matrix"),
  getModuleAccess: () => api.get("/auth/module-access", { timeout: 2000, iemsNoRetry: true }),
  changePassword: (data) => api.post("/auth/change-password", data),
  resetTempPassword: (email) => api.post("/auth/reset-temp-password", { email }),
  refresh: () => api.post("/auth/refresh", {}),
  logout: () => api.post("/auth/logout", {}),
};
