import { lazy } from "react";

export const EmployeeDirectoryPage = lazy(() => import("./pages/EmployeeDirectoryPage"));
export const EmployeeIdentityEditorPage = lazy(() => import("./pages/EmployeeIdentityEditorPage"));
export { employeeIdentityApi } from "./api/employeeIdentityApi";

export const EmployeeFilePage = lazy(() => import("./pages/EmployeeFilePage"));
export const EmployeeProfilePage = lazy(() => import("./pages/EmployeeProfilePage"));
export const EmployeeProfileEditorPage = lazy(() => import("./pages/EmployeeProfileEditorPage"));
export { default as EmployeeProfileSummary } from "./components/EmployeeProfileSummary";
export { employeeProfileApi } from "./api/employeeProfileApi";
export { resolveEmployeeProfileMediaUrl } from "./api/mediaUrls";
export {
  buildReferenceLabelMap,
  formatDirectoryEnumLabel,
  formatDirectoryFallbackLabel,
  formatWorkflowStatusLabel,
  resolveReferenceLabel,
} from "./lib/directoryLabels";
