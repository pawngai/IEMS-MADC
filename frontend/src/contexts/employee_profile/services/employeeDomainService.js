import { determineEmploymentType } from "@/contexts/service_book";

const normalizeStatus = (value, fallback) => {
  const normalized = String(value || "").trim().toUpperCase();
  return normalized || fallback;
};

export const normalizeEmployeeRecord = (employeeRecord) => {
  const normalized = { ...(employeeRecord || {}) };
  const employmentType = determineEmploymentType(normalized);
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

export const updateEmployeeStatus = (
  employeeRecord,
  { workflowStatus, serviceStatus } = {},
) => {
  const updated = normalizeEmployeeRecord(employeeRecord);

  if (workflowStatus !== undefined) {
    updated.workflow_status = normalizeStatus(workflowStatus, updated.workflow_status || "DRAFT");
  }

  if (serviceStatus !== undefined) {
    const normalizedServiceStatus = normalizeStatus(serviceStatus, "ACTIVE");
    updated.service_status = normalizedServiceStatus;
    updated.employee_status = normalizedServiceStatus;
  }

  return updated;
};
