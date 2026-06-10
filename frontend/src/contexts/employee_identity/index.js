import { lazy } from "react";

export const EmployeeDirectoryPage = lazy(() => import("./pages/EmployeeDirectoryPage"));
export const EmployeeIdentityEditorPage = lazy(() => import("./pages/EmployeeIdentityEditorPage"));
export { employeeIdentityApi } from "./api/employeeIdentityApi";
