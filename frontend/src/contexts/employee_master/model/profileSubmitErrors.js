export const resolveProfileSubmitError = ({ error, isEditMode }) => {
  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    const fieldErrors = {};
    detail.forEach((entry) => {
      const field = entry.loc?.[1] || entry.field || "unknown";
      fieldErrors[field] = entry.msg || entry.message || "Validation error";
    });
    const errorMessages = detail
      .map((entry) => entry.msg || entry.message)
      .filter(Boolean)
      .slice(0, 3);

    return {
      fieldErrors,
      toastMessage: `Validation failed: ${errorMessages.join(", ")}`,
    };
  }

  if (typeof detail === "object" && detail?.errors) {
    const fieldErrors = {};
    detail.errors.forEach((entry) => {
      fieldErrors[entry.field || entry.field_id] = entry.error || entry.message;
    });
    return {
      fieldErrors,
      toastMessage: detail.message || "Validation failed",
    };
  }

  if (typeof detail === "object" && detail?.message) {
    return {
      fieldErrors: null,
      toastMessage: detail.message,
    };
  }

  if (typeof detail === "string") {
    return {
      fieldErrors: null,
      toastMessage: detail,
    };
  }

  return {
    fieldErrors: null,
    toastMessage: isEditMode ? "Failed to update profile extension" : "Failed to save profile extension",
  };
};
