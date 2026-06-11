import { lazy } from "react";

export const DeptDashboardPage = lazy(() => import("./pages/DeptDashboardPage"));
export const DeptDirectoryPage = lazy(() => import("./pages/DeptDirectoryPage"));
export const DepartmentEmployeeFilePage = lazy(() => import("./pages/DepartmentEmployeeFilePage"));
export const DeptPendingWorkPage = lazy(() => import("./pages/DeptPendingWorkPage"));
export const DeptLeavePage = lazy(() => import("./pages/DeptLeavePage"));
export const DeptSanctionedStrengthPage = lazy(() => import("./pages/DeptSanctionedStrengthPage"));
export const DepartmentIdentityEditorPage = lazy(() =>
  import("./pages/DepartmentIdentityEditorPage")
);
export const DepartmentProfileEditorPage = lazy(() =>
  import("./pages/DepartmentProfileEditorPage")
);
export { departmentManagementAPI, mastersAPI, versionedMastersAPI } from "./api/mastersApi";
export { fetchDepartmentDashboard } from "./model/departmentHomeGateway";
