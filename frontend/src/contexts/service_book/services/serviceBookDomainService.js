import { projectionAPI } from "@/contexts/service_book/api/projectionApi";
import { printAPI } from "@/contexts/service_book/api/printApi";
import { isServiceBookEligible } from "@/contexts/service_book/services/serviceBookEligibility";
import { normalizeComplete } from "@/contexts/service_book/services/projectionNormalizer";

const buildNotApplicableError = () => {
  const error = new Error("Service Book is only maintained for REGULAR employees.");
  error.code = "SERVICE_BOOK_NOT_APPLICABLE";
  error.detail = {
    error: "Service Book not applicable",
    message: "Service Book is only maintained for REGULAR employees.",
    required_employment_type: "REGULAR",
  };
  return error;
};

export const validateServiceBookEligibility = (employeeOrType) => {
  if (!isServiceBookEligible(employeeOrType)) {
    throw buildNotApplicableError();
  }
  return true;
};

export const createServiceBookIfEligible = async ({ employeeId, employeeOrType }) => {
  validateServiceBookEligibility(employeeOrType);
  return projectionAPI.getComplete(employeeId);
};

export const rebuildServiceBookProjection = async ({ employeeId, employeeOrType, statuses }) => {
  validateServiceBookEligibility(employeeOrType);
  return projectionAPI.getComplete(employeeId, { statuses });
};

export const generateServiceBookPrintModel = async ({ employeeId, employeeOrType, statuses }) => {
  validateServiceBookEligibility(employeeOrType);
  let response;
  try {
    response = await projectionAPI.getComplete(employeeId, { statuses });
  } catch (error) {
    const status = error?.response?.status;
    if (status !== 403 || statuses?.length) {
      throw error;
    }
    const printResponse = await printAPI.printFull(employeeId);
    const groupedParts = printResponse?.data?.parts || {};
    const entries = Object.values(groupedParts).flatMap((items) => (
      Array.isArray(items) ? items : []
    ));
    response = {
      ...printResponse,
      data: normalizeComplete(employeeId, entries),
    };
  }
  return {
    generated_at: new Date().toISOString(),
    employee_id: employeeId,
    service_book: response?.data || {},
  };
};
