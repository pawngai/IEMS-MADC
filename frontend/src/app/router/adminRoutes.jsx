import { lazy } from "react";
import { Navigate, Route } from "react-router-dom";
import { Permissions } from "@/platform/permissions";
import { ProtectedRoute } from "@/app/router/guards";

const SystemAdminConsole = lazy(() => import("@/contexts/admin/pages/SystemAdminConsolePage"));
const SeniorityPage = lazy(() => import("@/contexts/seniority/pages/SeniorityPage"));
const AuditorDashboard = lazy(() => import("@/contexts/audit/pages/AuditorDashboardPage"));
const LeaveDashboard = lazy(() => import("@/contexts/leave/pages/LeaveDashboardPage"));
const AnalyticsDashboard = lazy(() => import("@/contexts/analytics/pages/AnalyticsDashboardPage"));

export const AdminRoutes = () => (
  <>
    <Route
      path="/leave"
      element={
        <ProtectedRoute
          requiredPermissions={[
            Permissions.LEAVE_READ_ALL,
            Permissions.LEAVE_RECOMMEND,
            Permissions.LEAVE_SANCTION,
          ]}
          moduleId="leave"
        >
          <LeaveDashboard />
        </ProtectedRoute>
      }
    />
    <Route path="/portal/leave" element={<Navigate to="/leave" replace />} />
    <Route
      path="/auditor"
      element={
        <ProtectedRoute requiredPermissions={[Permissions.AUDIT_READ_ALL]} moduleId="audit">
          <AuditorDashboard />
        </ProtectedRoute>
      }
    />
    <Route path="/portal/audit" element={<Navigate to="/auditor" replace />} />
    <Route
      path="/analytics"
      element={
        <ProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_ALL]}>
          <AnalyticsDashboard />
        </ProtectedRoute>
      }
    />
    <Route path="/portal/analytics" element={<Navigate to="/analytics" replace />} />
    <Route
      path="/admin"
      element={
        <ProtectedRoute
          requiredPermissions={[Permissions.USER_MANAGEMENT, Permissions.SYSTEM_CONFIG]}
          requireAllPermissions
          requiredAuthorities={["SYSTEM_ADMIN"]}
          moduleId="admin_console"
        >
          <SystemAdminConsole />
        </ProtectedRoute>
      }
    />
    <Route
      path="/admin/masters"
      element={
        <ProtectedRoute
          requiredPermissions={[Permissions.USER_MANAGEMENT, Permissions.SYSTEM_CONFIG]}
          requireAllPermissions
          requiredAuthorities={["SYSTEM_ADMIN"]}
          moduleId="admin_console"
        >
          <SystemAdminConsole />
        </ProtectedRoute>
      }
    />
    <Route
      path="/seniority"
      element={
        <ProtectedRoute
          requiredAuthorities={["SYSTEM_ADMIN", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "VERIFIER", "APPROVING_AUTHORITY"]}
        >
          <SeniorityPage />
        </ProtectedRoute>
      }
    />
  </>
);
