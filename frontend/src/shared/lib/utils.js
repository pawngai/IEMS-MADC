import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const SERVICE_BOOK_FIELD_LABELS = {
  name_in_block_letters: "Full Name",
  father_name: "Father's Name",
  nationality: "Nationality",
  caste_category: "Category",
  date_of_birth_christian: "Date of Birth",
  phone_number: "Mobile Number",
  employee_id: "Employee ID",
  employee_code: "Employee Code",
  employment_type: "Employment Type",
  date_of_initial_engagement: "Date of Appointment",
  current_department_id: "Department",
  employee_status: "Employee Status",
  family_members: "Family Members",
  pcf_nomination: "PCF Nominees",
  dcr_gratuity_nomination: "Gratuity Nominees",
};

export const formatServiceBookFieldLabel = (fieldKey) => {
  if (!fieldKey || typeof fieldKey !== "string") return "";
  return SERVICE_BOOK_FIELD_LABELS[fieldKey] || fieldKey;
};

export const getApiErrorMessage = (errorOrDetail, fallback = "Something went wrong") => {
  const detail = errorOrDetail?.response?.data?.detail ?? errorOrDetail?.detail ?? errorOrDetail;

  if (typeof detail === "string") {
    const trimmed = detail.trim();
    return trimmed || fallback;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => {
        if (typeof entry === "string") return entry;
        if (!entry || typeof entry !== "object") return null;
        if (typeof entry.msg === "string") return entry.msg;
        if (typeof entry.message === "string") return entry.message;
        return null;
      })
      .filter(Boolean);

    return messages.length ? messages.slice(0, 3).join("; ") : fallback;
  }

  if (detail && typeof detail === "object") {
    if (typeof detail.message === "string") return detail.message;
    if (typeof detail.msg === "string") return detail.msg;

    if (Array.isArray(detail.errors)) {
      const messages = detail.errors
        .map((entry) => {
          if (typeof entry === "string") return entry;
          if (!entry || typeof entry !== "object") return null;
          return entry.error || entry.message || entry.msg || null;
        })
        .filter(Boolean);
      if (messages.length) return messages.slice(0, 3).join("; ");
    }
  }

  return fallback;
};

export const formatDocumentMetadataErrorMessage = (errorOrDetail) => {
  const detail = errorOrDetail?.response?.data?.detail ?? errorOrDetail?.detail ?? errorOrDetail;
  if (!detail || typeof detail !== "object") return null;

  switch (detail.error_code) {
    case "DOCUMENT_ENTITY_TYPE_INVALID":
      return "This document link type is not supported.";
    case "DOCUMENT_ENTITY_ID_REQUIRED":
      return "Document link is incomplete: entity ID is required.";
    case "DOCUMENT_ENTITY_TYPE_REQUIRED":
      return "Document link is incomplete: entity type is required.";
    case "DOCUMENT_TYPE_INVALID":
      return "This document classification is not supported.";
    case "DOCUMENT_CATEGORY_INVALID":
      return "This document category is not valid.";
    case "DOCUMENT_SOURCE_CONTEXT_INVALID":
      return "This document source context is not valid.";
    case "DOCUMENT_SUPERSEDE_NOT_FOUND":
      return "The selected earlier document version could not be found.";
    case "DOCUMENT_SUPERSEDE_LOCKED":
      return "A locked document cannot be replaced with a new version.";
    case "DOCUMENT_VERSION_HISTORY_PROTECTED":
      return "Older document versions cannot be deleted after a newer version is linked.";
    case "DOCUMENT_METADATA_TRUTH_FORBIDDEN":
      return "Documents cannot define service-history truth.";
    default:
      return null;
  }
};

export const getLeaveTypeUnavailableMessage = ({
  userEmployeeId,
  profile,
  errorOrDetail,
} = {}) => {
  if (!userEmployeeId) {
    return "Your account is not linked to an employee profile, so leave types cannot be loaded.";
  }

  const detail = getApiErrorMessage(errorOrDetail, "");
  const normalized = typeof detail === "string" ? detail.trim() : "";

  if (
    normalized === "Employee profile not found" ||
    normalized === "No employee profile linked to user"
  ) {
    return "Your account is not linked to an employee profile, so leave types cannot be loaded.";
  }

  if (normalized === "Leave account not applicable for employment type") {
    return "Leave account is not available for your employment type.";
  }

  if (normalized) {
    return normalized;
  }

  if (!profile) {
    return "Your employee profile is not available, so leave types cannot be loaded.";
  }

  return "No leave types are available for your employment type.";
};

export const formatServiceBookPartsIncompleteMessage = (errorOrDetail) => {
  const detail = errorOrDetail?.response?.data?.detail ?? errorOrDetail?.detail ?? errorOrDetail;
  if (!detail || typeof detail !== "object") return null;
  if (detail.error_code !== "SERVICE_BOOK_PARTS_INCOMPLETE") return null;

  const baseMessage =
    typeof detail.message === "string" && detail.message.trim()
      ? detail.message.trim()
      : "Complete all required Service Book fields before submit.";

  const byPart = detail.missing_fields_by_part;
  if (!byPart || typeof byPart !== "object") return baseMessage;

  const partSummaries = Object.entries(byPart)
    .filter(([, fields]) => Array.isArray(fields) && fields.length > 0)
    .map(([part, fields]) => {
      const shown = fields.slice(0, 4).map(formatServiceBookFieldLabel).join(", ");
      const suffix = fields.length > 4 ? ` (+${fields.length - 4} more)` : "";
      return `${part}: ${shown}${suffix}`;
    });

  if (!partSummaries.length) return baseMessage;
  return `${baseMessage} ${partSummaries.join(" | ")}`;
};

export const getEmployeeCompletionStatus = (profile = {}) => {
  if (!profile || typeof profile !== "object") {
    return { complete: false, known: false };
  }

  const booleanFields = [
    "employee_section_completed",
    "employee_profile_completed",
    "profile_completed_by_employee",
    "self_service_completed",
    "ess_completed",
    "employee_completed",
    "is_profile_complete",
    "is_profile_completed",
    "profile_complete",
  ];

  for (const field of booleanFields) {
    if (typeof profile[field] === "boolean") {
      return { complete: profile[field], known: true };
    }
  }

  const percentFields = [
    "profile_completion_percent",
    "profile_completion_percentage",
    "profile_completion",
    "completion_percent",
    "completion_percentage",
    "completion",
    "employee_completion_percent",
  ];

  for (const field of percentFields) {
    const value = profile[field];
    if (typeof value === "number") {
      return { complete: value >= 100, known: true };
    }
    if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) {
      return { complete: Number(value) >= 100, known: true };
    }
  }

  const statusFields = [
    "profile_completion_status",
    "profile_completion_state",
    "self_service_status",
    "employee_section_status",
    "employee_profile_status",
  ];

  for (const field of statusFields) {
    const value = profile[field];
    if (typeof value === "string") {
      const normalized = value.toUpperCase();
      if (["COMPLETED", "COMPLETE", "DONE", "FINISHED", "SUBMITTED"].includes(normalized)) {
        return { complete: true, known: true };
      }
      if (["PENDING", "INCOMPLETE", "IN_PROGRESS", "DRAFT", "REJECTED"].includes(normalized)) {
        return { complete: false, known: true };
      }
    }
  }

  return { complete: true, known: false };
};

export const isEmployeeSectionComplete = (profile = {}) => getEmployeeCompletionStatus(profile).complete;

export const isDataEntrySectionComplete = (profile = {}) => !!profile?.data_entry_section_completed;

export const isBothSectionsComplete = (profile = {}) =>
  getEmployeeCompletionStatus(profile).complete && isDataEntrySectionComplete(profile);
