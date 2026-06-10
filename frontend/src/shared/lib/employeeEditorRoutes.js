import {
  scopeFromPath,
  employeeFilePath,
  employeeDirectoryPath,
  identityCreatePath,
  identityEditPath,
  profileEditPath,
} from "@/shared/lib/routes";

/**
 * Thin re-exports that delegate to the route registry.
 * Kept for backward-compat with existing call-sites.
 */
export const getEmployeeEditorScope = scopeFromPath;

export const buildEmployeeFilePath = employeeFilePath;

export const buildEmployeeDirectoryPath = employeeDirectoryPath;

export const buildIdentityCreatePath = identityCreatePath;

export const buildIdentityEditPath = identityEditPath;

export const buildProfileEditPath = profileEditPath;
