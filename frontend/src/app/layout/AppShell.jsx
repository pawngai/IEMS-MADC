import { Suspense } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { useAuth } from "@/contexts/identity_access";
import { PageLoader, RouteShellSkeleton } from "@/app/router/routeLoading";

/**
 * Authenticated app shell — a layout route. Renders the persistent chrome
 * (sidebar/header) once and streams page content through <Outlet/>, so lazy
 * page loads swap only the content area instead of remounting the shell.
 * Auth is checked here once; ProtectedRoute on child routes handles
 * permission/authority/module checks.
 */
const AppShell = () => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageLoader pathname={location.pathname} />;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <Layout>
      <Suspense fallback={<RouteShellSkeleton pathname={location.pathname} />}>
        <Outlet />
      </Suspense>
    </Layout>
  );
};

export default AppShell;
