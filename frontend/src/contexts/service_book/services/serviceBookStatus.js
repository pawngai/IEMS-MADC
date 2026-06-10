export const SERVICE_BOOK_STATUS = {
  NOT_APPLICABLE: "NOT_APPLICABLE",
  NOT_OPENED: "NOT_OPENED",
  OPENING_IN_PROGRESS: "OPENING_IN_PROGRESS",
  OPENED: "OPENED",
};

const pendingStatuses = new Set(["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED"]);

export const resolveServiceBookStatus = ({ summary, entries = [] }) => {
  if (summary && summary.eligible_for_service_book === false) {
    return {
      status: SERVICE_BOOK_STATUS.NOT_APPLICABLE,
      label: "Not Applicable",
      reason: "Current employment class is Non-Regular",
      canOpen: false,
    };
  }

  if (!summary?.eligible_for_service_book) {
    return {
      status: SERVICE_BOOK_STATUS.NOT_OPENED,
      label: "Not Opened",
      reason: "Service summary has not marked this employee as eligible yet.",
      canOpen: false,
    };
  }

  const normalizedEntries = Array.isArray(entries) ? entries : [];
  const hasOpenedEntry = normalizedEntries.some((entry) => String(entry?.workflow_state || entry?.status || "").toUpperCase() === "LOCKED");
  if (hasOpenedEntry) {
    return {
      status: SERVICE_BOOK_STATUS.OPENED,
      label: "Opened",
      reason: "Service Book has finalized entries.",
      canOpen: true,
    };
  }

  const hasPendingEntry = normalizedEntries.some((entry) => pendingStatuses.has(String(entry?.workflow_state || entry?.status || "").toUpperCase()));
  if (hasPendingEntry) {
    return {
      status: SERVICE_BOOK_STATUS.OPENING_IN_PROGRESS,
      label: "Opening In Progress",
      reason: "Service Book Opening is under process.",
      canOpen: true,
    };
  }

  return {
    status: SERVICE_BOOK_STATUS.NOT_OPENED,
    label: "Not Opened",
    reason: "Service Book can be opened for this regular employee.",
    canOpen: true,
  };
};