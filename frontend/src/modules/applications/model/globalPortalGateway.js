import { apiClient as api } from "@/platform/api/httpClient";

export const listProfilesByStatus = async (status, params = {}) => {
  const response = await api.get("/employee-profiles/", {
    params: {
      ...params,
      workflow_status: status,
      profile_workflow_only: true,
    },
  });
  return response?.data?.profiles || [];
};
