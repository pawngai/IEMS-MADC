export const OPENING_STATUS = {
  NOT_STARTED: "NOT_STARTED",
  DRAFT: "DRAFT",
  SUBMITTED: "SUBMITTED",
  VERIFIED: "VERIFIED",
  APPROVED: "APPROVED",
  LOCKED: "LOCKED",
  REJECTED: "REJECTED",
};

export const OPENING_STATUS_LABELS = {
  [OPENING_STATUS.NOT_STARTED]: "Not Started",
  [OPENING_STATUS.DRAFT]: "Draft",
  [OPENING_STATUS.SUBMITTED]: "Submitted",
  [OPENING_STATUS.VERIFIED]: "Verified",
  [OPENING_STATUS.APPROVED]: "Approved",
  [OPENING_STATUS.LOCKED]: "Opened",
  [OPENING_STATUS.REJECTED]: "Rejected",
};

export const normalizeOpeningStatus = (status) => {
  const normalized = String(status || "").trim().toUpperCase();
  if (!normalized) return OPENING_STATUS.NOT_STARTED;
  if (normalized === "NOT_OPENED") return OPENING_STATUS.NOT_STARTED;
  if (normalized === "OPENING_IN_PROGRESS") return OPENING_STATUS.DRAFT;
  if (normalized === "OPENED" || normalized === "ATTESTED") return OPENING_STATUS.LOCKED;
  return OPENING_STATUS[normalized] || normalized;
};

export const isOpeningFinal = (status) =>
  normalizeOpeningStatus(status) === OPENING_STATUS.LOCKED;

export const isOpeningEditable = (status) =>
  [OPENING_STATUS.NOT_STARTED, OPENING_STATUS.DRAFT, OPENING_STATUS.REJECTED].includes(
    normalizeOpeningStatus(status)
  );

export const getOpeningActionLabel = (status) => {
  const normalized = normalizeOpeningStatus(status);
  if (normalized === OPENING_STATUS.LOCKED) return "View Service Book";
  if (normalized === OPENING_STATUS.NOT_STARTED) return "Open Service Book";
  return "Continue Opening";
};
