import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '@/contexts/identity/api/authApi';
import { hasAuthority, hasAnyAuthority, Permissions, Authorities } from "@/contexts/identity/model/rbac";
import { canPerformAction, resolveScopeAccess, resolveUserPermissions } from "@/contexts/access_control";
import { getToken, getUser, setTokens, clearTokens } from "@/platform/api/httpClient";
import { AUTHORITY_DISPLAY_NAMES, AUTHORITY_PRIORITY } from "@/contexts/identity/model/authorityMeta";

const AuthContext = createContext(null);
const DEFAULT_MODULE_ACCESS = { mode: "deny_by_default", allowed_modules: [] };
const PUBLIC_AUTH_PATHS = new Set(["/login"]);

const _store = typeof sessionStorage !== 'undefined' ? sessionStorage : localStorage;
const AUTH_SESSION_NOTICE_KEY = 'iems_auth_notice';
let bootstrapRefreshPromise = null;

function normalizeAuthorityList(user) {
	return Array.from(new Set(Array.isArray(user?.authorities) ? user.authorities.filter(Boolean) : [])).sort();
}

export function hasAuthorityDrift(savedUser, freshUser) {
	const savedAuthorities = normalizeAuthorityList(savedUser);
	const freshAuthorities = normalizeAuthorityList(freshUser);
	if (savedAuthorities.length !== freshAuthorities.length) return true;
	return savedAuthorities.some((authority, index) => authority !== freshAuthorities[index]);
}

function persistAuthNotice(message) {
	try {
		_store.setItem(AUTH_SESSION_NOTICE_KEY, message);
	} catch { }
}

function getCurrentPathname() {
	if (typeof window === 'undefined') return '/';
	return window.location.pathname || '/';
}

function shouldAttemptBootstrapRefresh(pathname = getCurrentPathname()) {
	return !PUBLIC_AUTH_PATHS.has(pathname);
}

async function requestBootstrapRefresh() {
	if (!bootstrapRefreshPromise) {
		bootstrapRefreshPromise = authAPI.refresh().finally(() => {
			bootstrapRefreshPromise = null;
		});
	}
	return bootstrapRefreshPromise;
}

export const AuthProvider = ({ children }) => {
	const [user, setUser] = useState(null);
	const [loading, setLoading] = useState(true);
	const [moduleAccess, setModuleAccess] = useState(DEFAULT_MODULE_ACCESS);
	const [activeRole, setActiveRoleState] = useState(() => {
		try { return _store.getItem('iems_active_role') || null; } catch { return null; }
	});

	const setActiveRole = (role) => {
		setActiveRoleState(role);
		try {
			if (role) _store.setItem('iems_active_role', role);
			else _store.removeItem('iems_active_role');
		} catch { }
	};

	useEffect(() => {
		const bootstrapAuth = async () => {
			let token = getToken();
			let savedUser = getUser();

			if (!token && shouldAttemptBootstrapRefresh()) {
				try {
					const refreshResponse = await requestBootstrapRefresh();
					const { access_token, refresh_token, user: refreshedUser } = refreshResponse.data || {};
					if (access_token) {
						setTokens({ access_token, refresh_token, user: refreshedUser });
						token = access_token;
						savedUser = refreshedUser || savedUser;
					}
				} catch {
					clearTokens();
					setUser(null);
					setActiveRole(null);
					setModuleAccess(DEFAULT_MODULE_ACCESS);
					return;
				}
			}

			if (!token || !savedUser) {
				clearTokens();
				setUser(null);
				setActiveRole(null);
				setModuleAccess(DEFAULT_MODULE_ACCESS);
				return;
			}

			try {
				const res = await authAPI.getMe();
				if (res.data) {
					const freshUser = res.data;
					if (hasAuthorityDrift(savedUser, freshUser)) {
						clearTokens();
						persistAuthNotice('Your access changed. Sign in again to continue.');
						setUser(null);
						setActiveRole(null);
						setModuleAccess(DEFAULT_MODULE_ACCESS);
						return;
					}
					setTokens({ user: freshUser });
					const freshAuthorities = Array.isArray(freshUser?.authorities) ? freshUser.authorities : [];
					const savedRole = _store.getItem('iems_active_role');
					if (savedRole && !freshAuthorities.includes(savedRole)) {
						setActiveRole(null);
					}
					setUser(freshUser);
					return;
				}
			} catch {
				// fall through to clear stale auth state
			}

			clearTokens();
			setUser(null);
			setActiveRole(null);
			setModuleAccess(DEFAULT_MODULE_ACCESS);
			setLoading(false);
		};

		bootstrapAuth().finally(() => setLoading(false));
	}, []);

	useEffect(() => {
		const loadModuleAccess = async () => {
			try {
				const res = await authAPI.getModuleAccess();
				setModuleAccess(res.data || DEFAULT_MODULE_ACCESS);
			} catch {
				setModuleAccess(DEFAULT_MODULE_ACCESS);
			}
		};

		if (user) {
			loadModuleAccess();
		} else {
			setModuleAccess(DEFAULT_MODULE_ACCESS);
		}
	}, [user]);

	const login = async (email, password) => {
		const payload = {
			email: String(email || '').trim(),
			password: String(password || ''),
		};
		const response = await authAPI.login(payload);
		const { access_token, refresh_token, user: userData } = response.data;

		setTokens({ access_token, refresh_token, user: userData });
		setActiveRole(null);
		setUser(userData);

		return userData;
	};

	const logout = async () => {
		try {
			await authAPI.logout();
		} catch { }
		clearTokens();
		setActiveRole(null);
		setUser(null);
		setModuleAccess(DEFAULT_MODULE_ACCESS);
	};

	const clearMustChangePassword = () => {
		if (user) {
			const updated = { ...user, must_change_password: false };
			setTokens({ user: updated });
			setUser(updated);
		}
	};

	const can = (permission) => canPerformAction(user, { requiredPermissions: [permission] });
	const canAny = (permissions) => permissions.some((permission) => can(permission));
	const is = (authority) => hasAuthority(user, authority);
	const isAny = (authorities) => hasAnyAuthority(user, authorities);
	const getAccessScope = () => resolveScopeAccess(user).scope;
	const getResolvedPermissions = () => Array.from(resolveUserPermissions(user));
	const canAccessModule = (moduleId) => {
		if (!moduleId) return true;
		if (moduleAccess?.mode === "allow_all") return true;
		const allowedModules = Array.isArray(moduleAccess?.allowed_modules) ? moduleAccess.allowed_modules : [];
		if (moduleAccess?.mode === "deny_by_default") return allowedModules.includes(moduleId);
		return allowedModules.includes(moduleId);
	};
	const canAccessEssPortal = () => canAccessModule("ess_portal");

	const canVerify = () => can(Permissions.SERVICE_BOOK_ENTRY_VERIFY);
	const canApprove = () => can(Permissions.SERVICE_BOOK_ENTRY_APPROVE);
	const canAttest = () => can(Permissions.SERVICE_BOOK_ENTRY_ATTEST);
	const canAudit = () => can(Permissions.AUDIT_READ_ALL);
	const canCreateEntry = () => can(Permissions.SERVICE_BOOK_ENTRY_CREATE);
	const canSupersede = () => can(Permissions.SERVICE_BOOK_SUPERSEDE);

	const canCreateProfile = () => can(Permissions.PROFILE_CREATE);
	const canReadAllProfiles = () => can(Permissions.PROFILE_READ_ALL);
	const canUpdateProfile = () => canAny([Permissions.PROFILE_UPDATE_ALL, Permissions.PROFILE_UPDATE_OWN_LIMITED]);

	const getGlobalAuthorities = () => {
		if (!user?.authorities?.length) return [];
		return user.authorities.filter(a => a && a !== 'EMPLOYEE');
	};

	const getPrimaryAuthority = () => {
		if (!user?.authorities?.length) return 'EMPLOYEE';
		if (activeRole && user.authorities.includes(activeRole)) return activeRole;
		for (const auth of AUTHORITY_PRIORITY) {
			if (user.authorities.includes(auth)) return auth;
		}
		return user.authorities[0];
	};

	const getAuthorityDisplayName = (authority) => AUTHORITY_DISPLAY_NAMES[authority] || authority;

	return (
		<AuthContext.Provider value={{
			user,
			login,
			logout,
			loading,
			clearMustChangePassword,
			can,
			canAny,
			is,
			isAny,
			canVerify,
			canApprove,
			canAttest,
			canAudit,
			canCreateEntry,
			canSupersede,
			canCreateProfile,
			canReadAllProfiles,
			canUpdateProfile,
			canAccessModule,
			canAccessEssPortal,
			getAccessScope,
			getResolvedPermissions,
			getPrimaryAuthority,
			getAuthorityDisplayName,
			getGlobalAuthorities,
			activeRole,
			setActiveRole,
			Permissions,
			Authorities
		}}>
			{children}
		</AuthContext.Provider>
	);
};

export const useAuth = () => {
	const context = useContext(AuthContext);
	if (!context) {
		throw new Error('useAuth must be used within an AuthProvider');
	}
	return context;
};

export default AuthContext;
