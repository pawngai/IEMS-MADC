import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/identity";
import { usePermissions } from "@/contexts/identity_access";
import AccessDeniedPage from "@/app/pages/system-admin/AccessDeniedPage";
import { PageLoader } from "@/app/router/routeLoading";
import ForceChangePasswordDialog from "@/contexts/identity/ui/ForceChangePasswordDialog";

export const PasswordGate = ({ children }) => {
	const { user, logout, clearMustChangePassword } = useAuth();

	if (user?.must_change_password) {
		return (
			<ForceChangePasswordDialog
				user={user}
				onPasswordChanged={clearMustChangePassword}
				onLogout={logout}
			/>
		);
	}

	return children;
};

export const ProtectedRoute = ({
	children,
	requiredPermissions = [],
	moduleId = null,
	requireAllPermissions = false,
	requiredAuthorities = [],
	requireAllAuthorities = false,
}) => {
	const { user, loading } = useAuth();
	const { canAny, canAccessModule, isAny } = usePermissions();

	if (loading) return <PageLoader />;

	if (!user) {
		return <Navigate to="/login" replace />;
	}

	if (requiredPermissions.length > 0) {
		const hasAccess = requireAllPermissions
			? requiredPermissions.every((permission) => canAny([permission]))
			: canAny(requiredPermissions);
		if (!hasAccess) {
			return (
				<AccessDeniedPage description="You do not have the required permissions for this page." />
			);
		}
	}

	if (requiredAuthorities.length > 0) {
		const hasAuthorityAccess = requireAllAuthorities
			? requiredAuthorities.every((authority) => isAny([authority]))
			: isAny(requiredAuthorities);
		if (!hasAuthorityAccess) {
			return (
				<AccessDeniedPage description="Your current role does not allow access to this page." />
			);
		}
	}

	if (moduleId && !canAccessModule(moduleId)) {
		return (
			<AccessDeniedPage
				title="Module unavailable"
				description="This module is disabled for your role. Contact the system administrator if you need access."
			/>
		);
	}

	return children;
};
