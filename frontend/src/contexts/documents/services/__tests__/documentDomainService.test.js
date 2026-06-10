import { describe, expect, test } from "vitest";

import { validateDocumentMetadata } from "@/contexts/documents/services/documentDomainService";

describe("documentDomainService", () => {
  test("validates entity metadata and normalizes type", () => {
    const normalized = validateDocumentMetadata({ entity_type: "leave", entity_id: "L-1" });
    expect(normalized.entity_type).toBe("LEAVE");
    expect(normalized.entity_id).toBe("L-1");
  });

  test("normalizes optional document classification fields", () => {
    const normalized = validateDocumentMetadata({
      entity_type: "service-book",
      entity_id: "EMP-1",
      document_type: "certificate",
      category: "medical certificate",
      source_context: "Service Book.Upload",
    });

    expect(normalized.entity_type).toBe("SERVICE_BOOK");
    expect(normalized.document_type).toBe("CERTIFICATE");
    expect(normalized.category).toBe("MEDICAL_CERTIFICATE");
    expect(normalized.source_context).toBe("service_book.upload");
  });

  test("blocks service-history truth metadata", () => {
    expect(() =>
      validateDocumentMetadata({ entity_type: "LEAVE", entity_id: "L-1", service_history: true }),
    ).toThrow(/service-history truth/i);
  });

  test("rejects unsupported entity types", () => {
    expect(() =>
      validateDocumentMetadata({ entity_type: "payroll", entity_id: "PAY-1" }),
    ).toThrow(/allowed types/i);
  });

  test("rejects unsupported document types", () => {
    expect(() => validateDocumentMetadata({ document_type: "memo" })).toThrow(/allowed types/i);
  });

  test("rejects invalid source context format", () => {
    expect(() => validateDocumentMetadata({ source_context: "service/book" })).toThrow(
      /source_context/i,
    );
  });

  test("rejects invalid category format", () => {
    expect(() => validateDocumentMetadata({ category: "service/book" })).toThrow(/category/i);
  });

  test("preserves supersedes document id", () => {
    const normalized = validateDocumentMetadata({ supersedes_document_id: "doc-1" });
    expect(normalized.supersedes_document_id).toBe("doc-1");
  });

  test("requires entity_type when entity_id is provided", () => {
    expect(() =>
      validateDocumentMetadata({ entity_id: "L-1" }),
    ).toThrow(/entity_type is required when entity_id is provided/i);
  });

  test("normalizes dash-separated supported entity types", () => {
    const normalized = validateDocumentMetadata({ entity_type: "service-book", entity_id: "EMP-1" });
    expect(normalized.entity_type).toBe("SERVICE_BOOK");
  });

  test("accepts service record metadata used by Service Book Records", () => {
    const normalized = validateDocumentMetadata({ entity_type: "service-record", entity_id: "SE-1" });
    expect(normalized.entity_type).toBe("SERVICE_RECORD");
  });
});
