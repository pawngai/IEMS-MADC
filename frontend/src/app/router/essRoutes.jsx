import { lazy } from "react";
import { Navigate, Route } from "react-router-dom";
import { Permissions } from "@/contexts/identity/model/rbac";
import { useAuth } from "@/contexts/identity/model/authContext";
import { ESS_DOCUMENTS_REQUIRED_PERMISSIONS, hasEssEmployeeIdentity } from "@/contexts/ess/services/essDomainService";
import AccessDeniedPage from "@/app/pages/system-admin/AccessDeniedPage";
import { ProtectedRoute } from "@/app/router/guards";
import { PageLoader } from "@/app/router/routeLoading";

const EssDashboard = lazy(() => import("@/contexts/ess/pages/EssDashboardPage"));
const EssProfilePage = lazy(() => import("@/contexts/employee_profile/pages/EmployeeProfilePage"));
const EssDocumentsPage = lazy(() => import("@/contexts/ess/pages/EssDocumentsPage"));
const EssServiceBookPage = lazy(() => import("@/contexts/service_book/pages/EssServiceBookPage"));
const EssLeavePage = lazy(() => import("@/contexts/leave/pages/EssLeavePage"));
const EssNotificationsPage = lazy(() => import("@/contexts/notifications/pages/EssNotificationsPage"));
const EssChangeRequestsPage = lazy(() => import("@/contexts/change_requests/pages/EssChangeRequestsPage"));

const EssProtectedRoute = ({ requiredPermissions, children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <PageLoader />;
  }

  if (!hasEssEmployeeIdentity(user)) {
    return (
      <AccessDeniedPage
        title="ESS access denied"
        description="Employee Self-Service is available only to signed-in users linked to an employee account."
      />
    );
  }

  return (
    <ProtectedRoute
      requiredPermissions={requiredPermissions}
      requiredAuthorities={["EMPLOYEE"]}
      moduleId="ess_portal"
    >
      {children}
    </ProtectedRoute>
  );
};

export const EssRoutes = () => (
  <>
    <Route path="/ess" element={<Navigate to="/ess/dashboard" replace />} />
    <Route path="/ess/dashboard" element={<EssProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_OWN, Permissions.SERVICE_BOOK_READ_OWN]}><EssDashboard /></EssProtectedRoute>} />
    <Route path="/ess/profile" element={<EssProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_OWN, Permissions.PROFILE_READ_ALL]}><EssProfilePage /></EssProtectedRoute>} />
    <Route path="/ess/documents" element={<EssProtectedRoute requiredPermissions={ESS_DOCUMENTS_REQUIRED_PERMISSIONS}><EssDocumentsPage /></EssProtectedRoute>} />
    <Route path="/ess/service-book" element={<EssProtectedRoute requiredPermissions={[Permissions.SERVICE_BOOK_READ_OWN]}><EssServiceBookPage /></EssProtectedRoute>} />
    <Route path="/ess/leave" element={<EssProtectedRoute requiredPermissions={[Permissions.LEAVE_APPLY_OWN, Permissions.LEAVE_READ_OWN]}><EssLeavePage /></EssProtectedRoute>} />
    <Route path="/ess/notifications" element={<EssProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_OWN]}><EssNotificationsPage /></EssProtectedRoute>} />
    <Route path="/ess/change-requests" element={<EssProtectedRoute requiredPermissions={[Permissions.PROFILE_READ_OWN]}><EssChangeRequestsPage /></EssProtectedRoute>} />
  </>
);
