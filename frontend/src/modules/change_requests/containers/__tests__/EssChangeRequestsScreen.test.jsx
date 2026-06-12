import {
  canDeleteDocumentsForAuthority,
  formatDocumentSourceContextLabel,
  formatDocumentTypeLabel,
} from "@/modules/change_requests/containers/EssChangeRequestsScreen";

describe("EssChangeRequestsScreen document delete gating", () => {
  test("keeps delete disabled for ESS employee role on multi-role accounts", () => {
    expect(canDeleteDocumentsForAuthority("EMPLOYEE")).toBe(false);
  });

  test("enables delete for active department data entry role", () => {
    expect(canDeleteDocumentsForAuthority("DEPT_DATA_ENTRY")).toBe(true);
  });

  test("formats document type labels for the browser table", () => {
    expect(formatDocumentTypeLabel("CERTIFICATE")).toBe("Certificate");
    expect(formatDocumentTypeLabel("OFFICE_ORDER")).toBe("Office Order");
  });

  test("formats known and fallback source context labels", () => {
    expect(formatDocumentSourceContextLabel("change_requests.upload")).toBe("Change Request Upload");
    expect(formatDocumentSourceContextLabel("service_book.part_iia")).toBe("Service Book Part II-A");
    expect(formatDocumentSourceContextLabel("workflow.review_queue")).toBe("Workflow / Review Queue");
  });
});