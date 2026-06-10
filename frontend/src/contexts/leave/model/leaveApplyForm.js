export const COMMUTED_LEAVE_BASIS_OPTIONS = [
  { value: "MEDICAL", label: "Medical grounds" },
  { value: "STUDY_PUBLIC_INTEREST", label: "Approved public-interest study" },
];

export const createInitialLeaveApplyForm = () => ({
  leave_type_code: "",
  from_date: "",
  to_date: "",
  reason: "",
  leave_station: "",
  contact_during_leave: "",
  medical_certificate_provided: false,
  commuted_leave_basis: "",
  expected_delivery_date: "",
  childbirth_date: "",
  adoption_date: "",
  child_date_of_birth: "",
  child_has_disability: false,
  child_order: "",
  attachments: [],
});

export const isCommutedLeave = (leaveTypeCode) => leaveTypeCode === "CML";
export const isMaternityLeave = (leaveTypeCode) => leaveTypeCode === "ML";
export const isPaternityLeave = (leaveTypeCode) => leaveTypeCode === "PL";
export const isChildCareLeave = (leaveTypeCode) => leaveTypeCode === "CCL";

const LEAVE_DOCUMENT_TYPE_LABELS = Object.freeze({
  CERTIFICATE: "Certificate",
  ORDER: "Order",
});

export const getLeaveSupportingDocumentRecommendation = (form) => {
  if (isCommutedLeave(form.leave_type_code)) {
    if (form.commuted_leave_basis === "STUDY_PUBLIC_INTEREST") {
      return {
        documentType: "ORDER",
        documentTypeLabel: LEAVE_DOCUMENT_TYPE_LABELS.ORDER,
      };
    }
    return {
      documentType: "CERTIFICATE",
      documentTypeLabel: LEAVE_DOCUMENT_TYPE_LABELS.CERTIFICATE,
    };
  }

  if (isMaternityLeave(form.leave_type_code)) {
    return {
      documentType: "CERTIFICATE",
      documentTypeLabel: LEAVE_DOCUMENT_TYPE_LABELS.CERTIFICATE,
    };
  }

  if (isPaternityLeave(form.leave_type_code)) {
    if (form.adoption_date && !form.childbirth_date) {
      return {
        documentType: "ORDER",
        documentTypeLabel: LEAVE_DOCUMENT_TYPE_LABELS.ORDER,
      };
    }
    return {
      documentType: "CERTIFICATE",
      documentTypeLabel: LEAVE_DOCUMENT_TYPE_LABELS.CERTIFICATE,
    };
  }

  if (isChildCareLeave(form.leave_type_code)) {
    return {
      documentType: "CERTIFICATE",
      documentTypeLabel: LEAVE_DOCUMENT_TYPE_LABELS.CERTIFICATE,
    };
  }

  return null;
};

export const getLeaveSupportingDocumentRequirementMessage = (form) => {
  if (isCommutedLeave(form.leave_type_code)) {
    if (form.commuted_leave_basis === "STUDY_PUBLIC_INTEREST") {
      return "Commuted leave requires a supporting document: upload the approved public-interest study document.";
    }
    if (form.medical_certificate_provided) {
      return "Commuted leave requires a supporting document: upload the medical certificate.";
    }
    return "Commuted leave requires a supporting document: upload the medical certificate or approved public-interest study document.";
  }

  if (isMaternityLeave(form.leave_type_code)) {
    if (form.childbirth_date) {
      return "Maternity leave requires a supporting document: upload the childbirth record.";
    }
    return "Maternity leave requires a supporting document: upload the expected-delivery certificate.";
  }

  if (isPaternityLeave(form.leave_type_code)) {
    if (form.adoption_date && !form.childbirth_date) {
      return "Paternity leave requires a supporting document: upload the adoption record.";
    }
    return "Paternity leave requires a supporting document: upload the childbirth record.";
  }

  if (isChildCareLeave(form.leave_type_code)) {
    return "Child care leave requires a supporting document: upload proof of the child's date of birth.";
  }

  return null;
};

export const getLeaveEligibilityValidationMessage = (form) => {
  if (isCommutedLeave(form.leave_type_code)) {
    if (!form.medical_certificate_provided && form.commuted_leave_basis !== "STUDY_PUBLIC_INTEREST") {
      return "CML requires a medical certificate or public-interest study basis";
    }
  }

  if (isMaternityLeave(form.leave_type_code)) {
    if (!form.expected_delivery_date && !form.childbirth_date) {
      return "Maternity leave requires an expected delivery date or childbirth date";
    }
  }

  if (isPaternityLeave(form.leave_type_code)) {
    if (!form.childbirth_date && !form.adoption_date) {
      return "Paternity leave requires a childbirth date or adoption date";
    }
  }

  if (isChildCareLeave(form.leave_type_code)) {
    if (!form.child_date_of_birth) {
      return "Child care leave requires the child's date of birth";
    }
    if (form.child_order !== "" && Number(form.child_order) < 1) {
      return "Child order must be 1 or greater";
    }
  }

  return null;
};

export const getLeaveSupportingDocumentValidationMessage = (form) => {
  if ((form.attachments || []).length > 0) {
    return null;
  }
  return getLeaveSupportingDocumentRequirementMessage(form);
};

const toOptionalString = (value) => {
  const text = String(value ?? "").trim();
  return text ? text : null;
};

export const buildLeaveApplicationPayload = (form) => ({
  leave_type_code: form.leave_type_code,
  from_date: form.from_date,
  to_date: form.to_date,
  reason: form.reason,
  leave_station: toOptionalString(form.leave_station),
  contact_during_leave: form.contact_during_leave,
  medical_certificate_provided: Boolean(form.medical_certificate_provided),
  commuted_leave_basis: toOptionalString(form.commuted_leave_basis),
  expected_delivery_date: toOptionalString(form.expected_delivery_date),
  childbirth_date: toOptionalString(form.childbirth_date),
  adoption_date: toOptionalString(form.adoption_date),
  child_date_of_birth: toOptionalString(form.child_date_of_birth),
  child_has_disability: Boolean(form.child_has_disability),
  child_order: form.child_order === "" ? null : Number(form.child_order),
  attachments: (form.attachments || []).map((attachment) => ({
    url: attachment.url,
    filename: attachment.filename,
    original_name: attachment.original_name || null,
    file_size: Number.isFinite(Number(attachment.file_size)) ? Number(attachment.file_size) : null,
    content_type: attachment.content_type || null,
  })),
});