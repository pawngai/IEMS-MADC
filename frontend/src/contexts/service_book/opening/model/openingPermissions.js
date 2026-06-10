import { Permissions } from "@/platform/permissions";
import { OPENING_STATUS } from "@/contexts/service_book/opening/model/openingStatus";

export const SERVICE_BOOK_OPENING_PERMISSIONS = {
  CREATE: Permissions.SERVICE_BOOK_OPENING_CREATE,
  UPDATE: Permissions.SERVICE_BOOK_OPENING_UPDATE,
  SUBMIT: Permissions.SERVICE_BOOK_OPENING_SUBMIT,
  VERIFY: Permissions.SERVICE_BOOK_OPENING_VERIFY,
  APPROVE: Permissions.SERVICE_BOOK_OPENING_APPROVE,
};

export const resolveOpeningPermissions = ({ can, status, eligible }) => {
  const check = typeof can === "function" ? can : () => false;
  const normalizedStatus = String(status || OPENING_STATUS.NOT_STARTED).toUpperCase();
  const isEligible = eligible !== false;

  return {
    canCreate: isEligible && check(SERVICE_BOOK_OPENING_PERMISSIONS.CREATE),
    canUpdate:
      isEligible &&
      [OPENING_STATUS.NOT_STARTED, OPENING_STATUS.DRAFT, OPENING_STATUS.REJECTED].includes(normalizedStatus) &&
      (check(SERVICE_BOOK_OPENING_PERMISSIONS.UPDATE) || check(SERVICE_BOOK_OPENING_PERMISSIONS.CREATE)),
    canSubmit:
      isEligible &&
      [OPENING_STATUS.NOT_STARTED, OPENING_STATUS.DRAFT, OPENING_STATUS.REJECTED].includes(normalizedStatus) &&
      check(SERVICE_BOOK_OPENING_PERMISSIONS.SUBMIT),
    canVerify:
      isEligible &&
      normalizedStatus === OPENING_STATUS.SUBMITTED &&
      check(SERVICE_BOOK_OPENING_PERMISSIONS.VERIFY),
    canApprove:
      isEligible &&
      normalizedStatus === OPENING_STATUS.VERIFIED &&
      check(SERVICE_BOOK_OPENING_PERMISSIONS.APPROVE),
  };
};
