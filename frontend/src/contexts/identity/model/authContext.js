import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '@/contexts/identity/api/authApi';
import { getToken, getUser, setTokens, clearTokens } from "@/platform/api/httpClient";

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

	// AuthContext holds only auth state. Permission/authority/module selectors
	// live in @/contexts/identity_access (usePermissions); portal-access rules in
	// portalAccessRules. clearMustChangePassword is retained as an essential
	// auth-state transition that requires provider internals.
	return (
		<AuthContext.Provider value={{
			user,
			loading,
			login,
			logout,
			activeRole,
			setActiveRole,
			moduleAccess,
			clearMustChangePassword,
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
