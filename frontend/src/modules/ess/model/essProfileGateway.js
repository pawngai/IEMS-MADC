import { apiClient as api } from "@/platform/api/httpClient";

const EMPLOYMENT_TYPE_ALIASES = {
  REG: "REGULAR",
  REGULAR: "REGULAR",
  CONTRACT: "CONTRACTUAL",
  CONTRACTUAL: "CONTRACTUAL",
  DAILYWAGE: "DAILY_WAGE",
  DAILY_WAGE: "DAILY_WAGE",
  DEPUTATION: "DEPUTATION",
  REEMPLOYED: "REEMPLOYED",
  REEMPLOYMENT: "REEMPLOYED",
  OUTSOURCED: "OUTSOURCED",
};

const normalizeStatus = (value, fallback) => {
  const normalized = String(value || "").trim().toUpperCase();
  return normalized || fallback;
};

const normalizeEmploymentType = (profile) => {
  const raw = profile?.employment_type || profile?.employment_type_code;
  const normalized = String(raw || "").trim().toUpperCase();
  if (!normalized) return "";
  return EMPLOYMENT_TYPE_ALIASES[normalized] || normalized;
};

export const normalizeEssProfile = (employeeRecord) => {
  const normalized = { ...(employeeRecord || {}) };
  const employmentType = normalizeEmploymentType(normalized);
  const workflowStatus = normalizeStatus(normalized.workflow_status, "DRAFT");
  const serviceStatus = normalizeStatus(
    normalized.service_status || normalized.employee_status,
    "ACTIVE",
  );

  if (employmentType) normalized.employment_type = employmentType;
  normalized.workflow_status = workflowStatus;
  normalized.service_status = serviceStatus;
  normalized.employee_status = serviceStatus;

  return normalized;
};

export const getMyProfileAuditTrail = async (employeeId) => {
  const response = await api.get(`/employee-profiles/${employeeId}/audit-trail`);
  return response?.data?.audit_trail || [];
};