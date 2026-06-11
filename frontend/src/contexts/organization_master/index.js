import { lazy } from "react";

// TODO(context-migration): Move implementation from contexts/department and
// contexts/masters into contexts/organization_master once legacy imports are migrated.
export * from "@/contexts/department";
export { mastersAPI, departmentManagementAPI, versionedMastersAPI } from "@/contexts/masters";
export { fetchDepartmentDashboard } from "@/contexts/department/model/departmentHomeGateway";

export const DeptLeavePage = lazy(() => import("@/contexts/department/pages/DeptLeavePage"));
export const DeptSanctionedStrengthPage = lazy(() =>
  import("@/contexts/department/pages/DeptSanctionedStrengthPage")
);
export const DepartmentIdentityEditorPage = lazy(() =>
  import("@/contexts/department/pages/DepartmentIdentityEditorPage")
);
export const DepartmentProfileEditorPage = lazy(() =>
  import("@/contexts/department/pages/DepartmentProfileEditorPage")
);
