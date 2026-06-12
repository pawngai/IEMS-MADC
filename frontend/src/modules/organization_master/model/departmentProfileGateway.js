import { apiClient as api } from "@/platform/api/httpClient";
import { departmentPortalAPI } from "@/modules/organization_master/api/departmentApi";

export const getDepartmentProfile = async (employeeId) => {
  const response = await api.get(`/employee-profiles/${employeeId}`);
  return response?.data || null;
};

export const getDepartmentEmployeeFile = async (employeeId) => {
  try {
    return await getDepartmentProfile(employeeId);
  } catch (requestError) {
    const snapshotResponse = await departmentPortalAPI.getEmployeeSnapshot(employeeId);
    if (snapshotResponse?.data) {
      return snapshotResponse.data;
    }
    throw requestError;
  }
};

export const submitDepartmentProfile = async (employeeId, remarks) => {
  const response = await api.post(`/employee-profiles/${employeeId}/submit`, { remarks });
  return response?.data || null;
};

export const getDepartmentBulkProfileCompletion = async () => {
  const response = await api.get("/employee-profiles/completion/bulk");
  return response?.data || null;
};