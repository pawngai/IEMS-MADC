const {
  formatDocumentMetadataErrorMessage,
  formatServiceBookPartsIncompleteMessage,
  getLeaveTypeUnavailableMessage,
} = require("../utils");

describe("formatDocumentMetadataErrorMessage", () => {
  test("returns tailored messages for document metadata validation codes", () => {
    expect(
      formatDocumentMetadataErrorMessage({
        detail: { error_code: "DOCUMENT_ENTITY_TYPE_INVALID", message: "raw backend message" },
      })
    ).toBe("This document link type is not supported.");

    expect(
      formatDocumentMetadataErrorMessage({
        detail: { error_code: "DOCUMENT_ENTITY_ID_REQUIRED", message: "raw backend message" },
      })
    ).toBe("Document link is incomplete: entity ID is required.");

    expect(
      formatDocumentMetadataErrorMessage({
        detail: { error_code: "DOCUMENT_ENTITY_TYPE_REQUIRED", message: "raw backend message" },
      })
    ).toBe("Document link is incomplete: entity type is required.");

    expect(
      formatDocumentMetadataErrorMessage({
        detail: { error_code: "DOCUMENT_TYPE_INVALID", message: "raw backend message" },
      })
    ).toBe("This document classification is not supported.");

    expect(
      formatDocumentMetadataErrorMessage({
        detail: { error_code: "DOCUMENT_SOURCE_CONTEXT_INVALID", message: "raw backend message" },
      })
    ).toBe("This document source context is not valid.");

    expect(
      formatDocumentMetadataErrorMessage({
        detail: { error_code: "DOCUMENT_METADATA_TRUTH_FORBIDDEN", message: "raw backend message" },
      })
    ).toBe("Documents cannot define service-history truth.");
  });

  test("returns null for non-document metadata payloads", () => {
    expect(formatDocumentMetadataErrorMessage(null)).toBeNull();
    expect(
      formatDocumentMetadataErrorMessage({ detail: { error_code: "OTHER_ERROR", message: "No match" } })
    ).toBeNull();
  });
});

describe("formatServiceBookPartsIncompleteMessage", () => {
  test("returns null for non-matching error payloads", () => {
    expect(formatServiceBookPartsIncompleteMessage(null)).toBeNull();
    expect(formatServiceBookPartsIncompleteMessage({ detail: "plain error" })).toBeNull();
    expect(
      formatServiceBookPartsIncompleteMessage({
        detail: { error_code: "OTHER_ERROR", message: "No match" },
      })
    ).toBeNull();
  });

  test("formats part-wise missing fields from backend detail payload", () => {
    const message = formatServiceBookPartsIncompleteMessage({
      response: {
        data: {
          detail: {
            error_code: "SERVICE_BOOK_PARTS_INCOMPLETE",
            message:
              "Complete all profile fields required for Service Book Part I/II-A/II-B before submit.",
            missing_fields_by_part: {
              I: ["father_name", "date_of_birth_christian"],
              "II-A": ["current_department_id"],
              "II-B": [
                "family_members",
                "bank_account_number",
                "bank_name",
                "bank_ifsc",
                "nps_pran_number",
              ],
            },
          },
        },
      },
    });

    expect(message).toContain(
      "Complete all profile fields required for Service Book Part I/II-A/II-B before submit."
    );
    expect(message).toContain("I: Father's Name, Date of Birth");
    expect(message).toContain("II-A: Department");
    expect(message).toContain(
      "II-B: Family Members, bank_account_number, bank_name, bank_ifsc (+1 more)"
    );
  });
});

describe("getLeaveTypeUnavailableMessage", () => {
  test("explains when no linked employee profile exists", () => {
    expect(getLeaveTypeUnavailableMessage({ userEmployeeId: null })).toBe(
      "Your account is not linked to an employee profile, so leave types cannot be loaded."
    );

    expect(
      getLeaveTypeUnavailableMessage({
        userEmployeeId: "EST-001",
        errorOrDetail: { response: { data: { detail: "Employee profile not found" } } },
      })
    ).toBe("Your account is not linked to an employee profile, so leave types cannot be loaded.");
  });

  test("explains when leave account is not applicable", () => {
    expect(
      getLeaveTypeUnavailableMessage({
        userEmployeeId: "EMP-1",
        profile: { employee_id: "EMP-1" },
        errorOrDetail: { detail: "Leave account not applicable for employment type" },
      })
    ).toBe("Leave account is not available for your employment type.");
  });

  test("falls back to employment-type specific empty state", () => {
    expect(
      getLeaveTypeUnavailableMessage({
        userEmployeeId: "EMP-1",
        profile: { employee_id: "EMP-1" },
      })
    ).toBe("No leave types are available for your employment type.");
  });
});
