import { lazy } from "react";
import { Navigate, Route } from "react-router-dom";
import { ProtectedRoute } from "@/app/router/guards";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import AccessDeniedPage from "@/app/pages/system-admin/AccessDeniedPage";
import { getDefaultLandingPath } from "@/app/router/defaultLanding";
import LoginPage from "@/contexts/identity_access/ui/LoginPage";

const GlobalPortalDashboard = lazy(() => import("@/contexts/applications/pages/GlobalPortalDashboardPage"));
const NotFoundPage = lazy(() => import("@/app/pages/system-admin/NotFoundPage"));

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

export const PublicRoutes = () => (
	<>
		<Route path="/login" element={<LoginPage />} />
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
				<ProtectedRoute>
					<GlobalPortalDashboard />
				</ProtectedRoute>
			}
		/>

		<Route path="*" element={<NotFoundPage />} />
	</>
);
