import { lazy } from "react";
import { Navigate, Route } from "react-router-dom";
import { ProtectedRoute } from "@/app/router/guards";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import { Permissions } from "@/platform/permissions";
import AccessDeniedPage from "@/app/pages/system-admin/AccessDeniedPage";
import { getDefaultLandingPath } from "@/contexts/identity_access";
import LoginPage from "@/contexts/identity_access/ui/LoginPage";

const GlobalPortalDashboard = lazy(() => import("@/contexts/applications/pages/GlobalPortalDashboardPage"));
const NotFoundPage = lazy(() => import("@/app/pages/system-admin/NotFoundPage"));

/**
 * The operations dashboard surfaces directory, work-queue, leave-workflow and
 * audit entry points; any one of these permissions marks an operations user.
 * EMPLOYEE-only accounts hold none of them and are denied.
 */
const OPERATIONS_DASHBOARD_PERMISSIONS = [
	Permissions.PROFILE_READ_ALL,
	Permissions.PROFILE_CREATE,
	Permissions.PROFILE_UPDATE_ALL,
	Permissions.SERVICE_BOOK_READ_ALL,
	Permissions.SERVICE_BOOK_ENTRY_CREATE,
	Permissions.LEAVE_RECOMMEND,
	Permissions.LEAVE_SANCTION,
	Permissions.AUDIT_READ_ALL,
];

/** Resolve a role-aware landing page for the signed-in user. */
const DefaultLanding = () => {
	const { user } = useAuth();
	const permissions = usePermissions();
	const landingPath = getDefaultLandingPath({ user, ...permissions });

	if (!landingPath) {
		return (
			<AccessDeniedPage
				title="No accessible portal"
				description="Your account is signed in, but there is no enabled portal for your current role set."
			/>
		);
	}

	return <Navigate to={landingPath} replace />;
};

/** Routes that render inside the authenticated AppShell layout route. */
export const LandingRoutes = () => (
	<>
		<Route
			path="/"
			element={
				<ProtectedRoute>
					<DefaultLanding />
				</ProtectedRoute>
			}
		/>
		<Route
			path="/home"
			element={
				<ProtectedRoute>
					<DefaultLanding />
				</ProtectedRoute>
			}
		/>

		<Route path="/portal" element={<Navigate to="/portal/dashboard" replace />} />
		<Route
			path="/portal/dashboard"
			element={
				<ProtectedRoute requiredPermissions={OPERATIONS_DASHBOARD_PERMISSIONS}>
					<GlobalPortalDashboard />
				</ProtectedRoute>
			}
		/>
	</>
);

/** Routes that render outside the AppShell (no sidebar/header chrome). */
export const PublicRoutes = () => (
	<>
		<Route path="/login" element={<LoginPage />} />
		<Route path="*" element={<NotFoundPage />} />
	</>
);
