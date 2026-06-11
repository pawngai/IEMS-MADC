/**
 * Identity Access — permission selectors.
 *
 * Centralizes RBAC permission/authority/module checks. The AuthContext now holds
 * only auth state (user, loading, login, logout, activeRole, setActiveRole,
 * moduleAccess); permission logic lives here.
 *
 * Usage:
 *   const { can, canAny, canAccessModule, getPrimaryAuthority } = usePermissions();
 */
import { useAuth } from "@/contexts/identity_access";
import { createPermissionSelectors } from "@/platform/permissions";

/**
 * Hook returning permission selectors derived from current auth state.
 * Selector surface: can, canAny, canAll, isAny, canAccessModule,
 * canAccessEssPortal, canAccessAdminPortal, getPrimaryAuthority,
 * getAuthorityDisplayName, Permissions, ...
 */
const SELECTOR_KEYS = [
  "can", "canAny", "canAll", "isAny", "canAccessModule", "canAccessEssPortal",
  "canAccessAdminPortal", "getPrimaryAuthority", "getAuthorityDisplayName",
];

export function usePermissions() {
  const auth = useAuth() || {};
  const { user, moduleAccess, activeRole } = auth;
  const computed = createPermissionSelectors({ user, moduleAccess, activeRole });
  // Transitional test-compat: surface any selector functions already present on
  // the auth value. The production AuthContext exposes none (it is minimized), so
  // this is a no-op in the app; it only lets tests that still mock selectors on
  // useAuth keep working until they migrate to mocking usePermissions directly.
  // COMPAT: removable once page tests mock usePermissions.
  const provided = {};
  for (const key of SELECTOR_KEYS) {
    if (typeof auth[key] === "function") provided[key] = auth[key];
  }
  return { ...computed, ...provided };
}

// Pure factory re-export for non-hook callers (tests, services).
export { createPermissionSelectors } from "@/platform/permissions";
