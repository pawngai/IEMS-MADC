import { departmentPortalAPI } from "@/contexts/organization_master/api/departmentApi";

export const fetchDepartmentDashboard = () => departmentPortalAPI.getDashboard();
