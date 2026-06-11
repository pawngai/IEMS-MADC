/**
 * Portal landing rules. The implementation now lives in identity_access (RBAC and
 * portal access are centralized there); this module re-exports for back-compat.
 * COMPAT: callers should import from @/contexts/identity_access.
 */
export {
  getEssHomePath,
  canEnterEssPortal,
  getDefaultLandingPath,
} from "@/contexts/identity_access/model/portalAccessRules";
