import { OPENING_STEPS } from "@/modules/service_book/opening/model/openingSteps";
import {
  OPENING_STATUS,
  getOpeningActionLabel,
  normalizeOpeningStatus,
} from "@/modules/service_book/opening/model/openingStatus";

const REGULAR_ALIASES = new Set(["REG", "REGULAR"]);

export const isRegularEmployeeForOpening = (employee) => {
  if (employee && "eligible_for_service_book" in employee) {
    return Boolean(employee.eligible_for_service_book);
  }
  const employmentType = String(
    employee?.current_employment_type_code ||
      employee?.employment_type ||
      employee?.employment_type_code ||
      employee?.current_employment_class ||
      ""
  )
    .trim()
    .toUpperCase();
  return REGULAR_ALIASES.has(employmentType);
};

export const buildOpeningEligibility = (employee) => {
  const eligible = isRegularEmployeeForOpening(employee);
  return {
    eligible,
    reason: eligible
      ? "Service Book Opening is available for this regular employee."
      : "Service Book Opening is only available for REGULAR employees.",
  };
};

export const getOpeningStatus = (opening) =>
  normalizeOpeningStatus(opening?.status || opening?.workflow_status);

export const getOpeningCta = (opening) => {
  const status = getOpeningStatus(opening);
  return {
    status,
    label: getOpeningActionLabel(status),
    target: status === OPENING_STATUS.LOCKED ? "service_book" : "opening",
  };
};

const isPlainObject = (value) => Boolean(value) && typeof value === "object" && !Array.isArray(value);

const hasMeaningfulValue = (value) => {
  if (value === undefined || value === null) return false;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return !Number.isNaN(value);
  if (typeof value === "string") {
    const normalized = value.trim();
    return normalized !== "" && normalized !== "[]" && normalized !== "{}";
  }
  if (Array.isArray(value)) {
    return value.some((item) => hasMeaningfulValue(item));
  }
  if (isPlainObject(value)) {
    return Object.values(value).some((item) => hasMeaningfulValue(item));
  }
  return true;
};

const hasCustomOpeningCompletion = (part, step) => {
  if (step?.id === "part_iib" || step?.id === "part_iii") {
    return hasMeaningfulValue(part || {});
  }
  return null;
};

export const isOpeningPartComplete = (part, step) => {
  const source = part || {};
  const customCompletion = hasCustomOpeningCompletion(source, step);
  if (typeof customCompletion === "boolean") {
    return customCompletion;
  }
  return (step?.requiredFields || []).every((field) => {
    const value = source[field];
    return value !== undefined && value !== null && String(value).trim() !== "";
  });
};

export const getOpeningCompletion = (draft = {}) => {
  const safeDraft = draft || {};
  const parts = safeDraft.parts || safeDraft;
  const byStep = Object.fromEntries(
    OPENING_STEPS.map((step) => [step.id, isOpeningPartComplete(parts?.[step.id], step)])
  );
  return {
    byStep,
    complete: OPENING_STEPS.every((step) => byStep[step.id]),
  };
};

export const canSubmitOpeningDraft = (draft) => getOpeningCompletion(draft).complete;
