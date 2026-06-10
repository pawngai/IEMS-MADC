export {
  Authorities,
  EmploymentTypes,
  Permissions,
  WorkflowStages,
  hasAnyAuthority,
  hasAuthority,
  normalizeWorkflowStage,
} from "@/platform/permissions";

export const hasPermission = (user, permission) =>
  user?.permissions?.includes(permission) || false;

export const hasAnyPermission = (user, permissions) =>
  permissions.some((permission) => user?.permissions?.includes(permission));
