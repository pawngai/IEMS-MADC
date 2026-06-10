import { describe, test, expect, vi, beforeEach } from "vitest";

const mockGet = vi.fn();

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  apiClient: { get: (...args) => mockGet(...args) },
  API_URL: "http://test/api",
}));

vi.mock("@/contexts/documents/services/documentDomainService", () => ({
  __esModule: true,
  attachDocumentToEntity: vi.fn(),
  validateDocumentMetadata: vi.fn(),
}));

import { documentsAPI } from "@/contexts/documents/api/documentsApi";

beforeEach(() => {
  mockGet.mockReset();
  mockGet.mockResolvedValue({ data: new Blob(["payload"], { type: "application/pdf" }) });

  if (typeof window !== "undefined") {
    window.URL.createObjectURL = vi.fn(() => "blob:mock");
    window.URL.revokeObjectURL = vi.fn();
  }
});

describe("documentsAPI.openDocument", () => {
  test("streams /documents/files/<filename> through the authenticated apiClient", async () => {
    const anchorClick = vi.fn();
    const realCreate = window.document.createElement.bind(window.document);
    const createSpy = vi.spyOn(window.document, "createElement").mockImplementation((tag) => {
      const el = realCreate(tag);
      if (tag === "a") {
        el.click = anchorClick;
      }
      return el;
    });

    await documentsAPI.openDocument("invoice.pdf");

    expect(mockGet).toHaveBeenCalledWith(
      "/documents/files/invoice.pdf",
      expect.objectContaining({ responseType: "blob" }),
    );
    expect(window.URL.createObjectURL).toHaveBeenCalled();
    expect(anchorClick).toHaveBeenCalledTimes(1);
    createSpy.mockRestore();
  });

  test("opens via a target=_blank anchor and never navigates the current tab", async () => {
    const locationAssign = vi.fn();
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...originalLocation, assign: locationAssign, set href(_) { locationAssign(_); } },
    });
    const realCreate = window.document.createElement.bind(window.document);
    let createdAnchor = null;
    const createSpy = vi.spyOn(window.document, "createElement").mockImplementation((tag) => {
      const el = realCreate(tag);
      if (tag === "a") {
        el.click = vi.fn();
        createdAnchor = el;
      }
      return el;
    });

    await documentsAPI.openDocument("invoice.pdf");

    expect(createdAnchor?.target).toBe("_blank");
    expect(createdAnchor?.rel).toBe("noopener noreferrer");
    expect(locationAssign).not.toHaveBeenCalled();

    createSpy.mockRestore();
    Object.defineProperty(window, "location", { configurable: true, value: originalLocation });
  });
});

describe("documentsAPI.downloadDocument", () => {
  test("streams /documents/files/<filename>/download through the authenticated apiClient", async () => {
    await documentsAPI.downloadDocument("invoice.pdf");

    expect(mockGet).toHaveBeenCalledWith(
      "/documents/files/invoice.pdf/download",
      expect.objectContaining({ responseType: "blob" }),
    );
    expect(window.URL.createObjectURL).toHaveBeenCalled();
  });

  test("applies suggestedName as the anchor download attribute", async () => {
    const anchorClick = vi.fn();
    const realCreate = window.document.createElement.bind(window.document);
    const createSpy = vi.spyOn(window.document, "createElement").mockImplementation((tag) => {
      const el = realCreate(tag);
      if (tag === "a") {
        el.click = anchorClick;
      }
      return el;
    });

    await documentsAPI.downloadDocument("hash-abc.pdf", { suggestedName: "Engagement Order.pdf" });

    expect(anchorClick).toHaveBeenCalledTimes(1);
    createSpy.mockRestore();
  });
});
