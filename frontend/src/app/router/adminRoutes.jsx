import { Navigate, Route } from "react-router-dom";
import { Permissions } from "@/platform/permissions";
import { ProtectedRoute } from "@/app/router/guards";
import { LeaveDashboardPage as LeaveDashboard } from "@/contexts/leave_attendance";
import { AnalyticsDashboardPage as AnalyticsDashboard } from "@/contexts/reporting_analytics";
import { SystemAdminConsolePage as SystemAdminConsole } from "@/contexts/admin";
import { SeniorityPage } from "@/contexts/seniority";
import { AuditorDashboardPage as AuditorDashboard } from "@/contexts/audit";

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
      path="/admin/:tab"
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
