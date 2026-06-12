import { departmentPortalAPI } from "@/modules/organization_master/api/departmentApi";

export const fetchDepartmentDashboard = () => departmentPortalAPI.getDashboard();
