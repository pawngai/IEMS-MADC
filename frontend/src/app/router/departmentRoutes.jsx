import { lazy } from "react";
import { Navigate, Route } from "react-router-dom";
import {
  DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES,
  DEPARTMENT_SCOPED_AUTHORITIES,
} from "@/platform/permissions";
import { Permissions } from "@/platform/permissions";
import { ProtectedRoute } from "@/app/router/guards";

const DeptDashboard = lazy(() => import("@/contexts/department/pages/DeptDashboardPage"));
const DeptDirectoryPage = lazy(() => import("@/contexts/department/pages/DeptDirectoryPage"));
const DeptPendingWorkPage = lazy(() => import("@/contexts/department/pages/DeptPendingWorkPage"));
const DeptLeavePage = lazy(() => import("@/contexts/department/pages/DeptLeavePage"));
const DeptSanctionedStrengthPage = lazy(() => import("@/contexts/department/pages/DeptSanctionedStrengthPage"));
const DepartmentEmployeeFile = lazy(() => import("@/contexts/department/pages/DepartmentEmployeeFilePage"));
const DepartmentIdentityEditorPage = lazy(() => import("@/contexts/department/pages/DepartmentIdentityEditorPage"));
const DepartmentProfileEditorPage = lazy(() => import("@/contexts/department/pages/DepartmentProfileEditorPage"));

const IDENTITY_EDITOR_PERMISSIONS = [
  Permissions.IDENTITY_READ_ALL,
  Permissions.IDENTITY_CREATE,
  Permissions.IDENTITY_UPDATE_ALL,
];

export const DepartmentRoutes = () => (
  <>
    <Route path="/department-portal" element={<Navigate to="/department-portal/dashboard" replace />} />
    <Route path="/department-portal/dashboard" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DeptDashboard /></ProtectedRoute>} />
    <Route path="/department-portal/directory" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DeptDirectoryPage /></ProtectedRoute>} />
    <Route path="/department-portal/pending-work" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DeptPendingWorkPage /></ProtectedRoute>} />
    <Route path="/department-portal/leave" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DeptLeavePage /></ProtectedRoute>} />
    <Route path="/department-portal/sanctioned-strength" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DeptSanctionedStrengthPage /></ProtectedRoute>} />
    <Route path="/department-portal/employees/new/identity" element={<ProtectedRoute requiredPermissions={IDENTITY_EDITOR_PERMISSIONS} requiredAuthorities={DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES}><DepartmentIdentityEditorPage /></ProtectedRoute>} />
    <Route path="/department-portal/employee/:employeeId" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DepartmentEmployeeFile /></ProtectedRoute>} />
    <Route path="/department-portal/employee/:employeeId/identity/edit" element={<ProtectedRoute requiredPermissions={IDENTITY_EDITOR_PERMISSIONS} requiredAuthorities={DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES}><DepartmentIdentityEditorPage /></ProtectedRoute>} />
    <Route path="/department-portal/employee/:employeeId/profile/edit" element={<ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]} requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}><DepartmentProfileEditorPage /></ProtectedRoute>} />
  </>
);
