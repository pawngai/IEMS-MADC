import { isServiceBookEligible } from "@/contexts/service_book";

const DOCUMENT_READ_OWN_PERMISSION = "DOCUMENT_READ_OWN";

export const ESS_DOCUMENTS_REQUIRED_PERMISSIONS = [DOCUMENT_READ_OWN_PERMISSION];

export const hasEssEmployeeIdentity = (user) => {
  const authorities = Array.isArray(user?.authorities) ? user.authorities : [];
  const employeeId = String(user?.employee_id || "").trim();
  return authorities.includes("EMPLOYEE") && Boolean(employeeId);
};

export const assertEssPortalSession = ({ user }) => {
  if (!hasEssEmployeeIdentity(user)) {
    throw new Error("ESS portal requires a linked employee account");
  }
  return true;
};

export const assertEssSelfScope = ({ user, targetEmployeeId }) => {
  assertEssPortalSession({ user });
  const currentEmployeeId = String(user?.employee_id || "").trim();
  const target = String(targetEmployeeId || currentEmployeeId).trim();
  if (!currentEmployeeId || !target || currentEmployeeId !== target) {
    throw new Error("ESS actions are restricted to self scope");
  }
  return true;
};

export const canShowEssServiceBook = ({ profile, user }) => {
  assertEssSelfScope({ user, targetEmployeeId: profile?.employee_id || user?.employee_id });
  return isServiceBookEligible(profile);
};

export const canAccessEssDocuments = ({ user, can }) => {
  if (!hasEssEmployeeIdentity(user) || typeof can !== "function") return false;
  return ESS_DOCUMENTS_REQUIRED_PERMISSIONS.some((permission) => can(permission));
};
