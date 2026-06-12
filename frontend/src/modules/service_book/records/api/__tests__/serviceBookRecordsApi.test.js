import { beforeEach, describe, expect, test, vi } from "vitest";

const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();
const mockApiGet = vi.fn();

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  apiClient: {
    post: (...args) => mockApiPost(...args),
    patch: (...args) => mockApiPatch(...args),
    get: (...args) => mockApiGet(...args),
  },
}));

import { serviceBookRecordsAPI } from "@/modules/service_book/records/api/serviceBookRecordsApi";

describe("serviceBookRecordsAPI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("recordEvent posts to canonical Service Book records endpoint", async () => {
    mockApiPost.mockResolvedValueOnce({ data: { ok: true } });
    const payload = {
      employee_id: "EMP-100",
      event_type: "PROMOTION",
      payload: { order_no: "PROMO-1" },
    };

    await serviceBookRecordsAPI.recordEvent(payload);

    expect(mockApiPost).toHaveBeenCalledWith("/service-book/records", payload);
  });

  test("correctEvent patches path-based event id endpoint", async () => {
    mockApiPatch.mockResolvedValueOnce({ data: { ok: true } });
    const payload = { corrected_payload: { to_post: "AO" }, reason: "typo" };

    await serviceBookRecordsAPI.correctEvent("SE-1", payload);

    expect(mockApiPatch).toHaveBeenCalledWith("/service-book/records/SE-1/correct", payload);
  });

  test("voidEvent and attachDocument post to action endpoints", async () => {
    mockApiPost.mockResolvedValue({ data: { ok: true } });

    await serviceBookRecordsAPI.voidEvent("SE-2", { reason: "superseded" });
    await serviceBookRecordsAPI.attachDocument("SE-2", { document_id: "DOC-1" });

    expect(mockApiPost).toHaveBeenCalledWith("/service-book/records/SE-2/void", { reason: "superseded" });
    expect(mockApiPost).toHaveBeenCalledWith("/service-book/records/SE-2/documents", { document_id: "DOC-1" });
  });

  test("listAccessibleDocuments reads through the documents endpoint", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { items: [] } });

    await serviceBookRecordsAPI.listAccessibleDocuments({ query: "promotion", limit: 12, offset: 0 });

    expect(mockApiGet).toHaveBeenCalledWith("/documents/files", {
      params: { query: "promotion", limit: 12, offset: 0 },
    });
  });

  test("uploadLinkedDocument posts multipart uploads through the documents endpoint", async () => {
    mockApiPost.mockResolvedValueOnce({ data: { ok: true } });
    const file = new File(["pdf"], "order.pdf", { type: "application/pdf" });

    await serviceBookRecordsAPI.uploadLinkedDocument(file, {
      entity_type: "SERVICE_RECORD",
      entity_id: "SE-2",
      document_type: "ORDER",
      source_context: "service_book.records.attach",
    });

    expect(mockApiPost).toHaveBeenCalledWith(
      "/documents/document?entity_type=SERVICE_RECORD&entity_id=SE-2&document_type=ORDER&source_context=service_book.records.attach",
      expect.any(FormData),
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
  });

  test("getEventStream resolves employee timeline endpoint", async () => {
    mockApiGet.mockResolvedValueOnce({ data: [] });

    await serviceBookRecordsAPI.getEventStream("EMP-100");

    expect(mockApiGet).toHaveBeenCalledWith("/service-book/records/employees/EMP-100");
  });

  test("getRecordSchema resolves schema endpoint", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { event_subtype_options: [] } });

    await serviceBookRecordsAPI.getRecordSchema();

    expect(mockApiGet).toHaveBeenCalledWith("/service-book/records/schema");
  });
});
