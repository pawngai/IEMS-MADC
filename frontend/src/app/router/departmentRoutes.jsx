import { Navigate, Route } from "react-router-dom";
import {
  DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES,
  DEPARTMENT_SCOPED_AUTHORITIES,
} from "@/platform/permissions";
import { Permissions } from "@/platform/permissions";
import { ProtectedRoute } from "@/app/router/guards";
import {
  DepartmentEmployeeFilePage as DepartmentEmployeeFile,
  DepartmentIdentityEditorPage,
  DepartmentProfileEditorPage,
  DeptDashboardPage as DeptDashboard,
  DeptDirectoryPage,
  DeptLeavePage,
  DeptPendingWorkPage,
  DeptSanctionedStrengthPage,
} from "@/contexts/organization_master";

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
