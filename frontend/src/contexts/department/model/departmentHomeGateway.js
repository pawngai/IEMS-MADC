import { departmentPortalAPI } from "@/contexts/department/api/departmentApi";

export const fetchDepartmentDashboard = () => departmentPortalAPI.getDashboard();
