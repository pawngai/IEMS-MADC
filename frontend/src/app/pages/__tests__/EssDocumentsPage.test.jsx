import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import EssDocumentsPage from "@/contexts/ess/pages/EssDocumentsPage";

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
  },
}));

const mockGetMyDocuments = jest.fn();
const mockPreviewMyDocument = jest.fn();
const mockDownloadMyDocument = jest.fn();
let anchorClickSpy;

jest.mock("@/contexts/ess/api/essApi", () => ({
  __esModule: true,
  essAPI: {
    getMyDocuments: (...args) => mockGetMyDocuments(...args),
    previewMyDocument: (...args) => mockPreviewMyDocument(...args),
    downloadMyDocument: (...args) => mockDownloadMyDocument(...args),
  },
}));

describe("EssDocumentsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    anchorClickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    window.open = jest.fn(() => ({ location: { replace: jest.fn() }, close: jest.fn() }));
    URL.createObjectURL = jest.fn(() => "blob:test-document");
    URL.revokeObjectURL = jest.fn();
    mockPreviewMyDocument.mockResolvedValue({
      data: new Blob(["preview"], { type: "application/pdf" }),
      headers: { "content-type": "application/pdf" },
    });
    mockDownloadMyDocument.mockResolvedValue({
      data: new Blob(["download"], { type: "application/pdf" }),
      headers: { "content-type": "application/pdf" },
    });
    mockGetMyDocuments.mockResolvedValue({
      data: {
        total: 1,
        available_filters: {
          document_types: ["ORDER"],
          source_contexts: ["service_book.records.upload"],
        },
        items: [
          {
            document_id: "doc-1",
            filename: "doc-1.pdf",
            original_name: "Appointment Order.pdf",
            document_type: "ORDER",
            category: "APPOINTMENT_ORDER",
            source_context: "service_book.records.upload",
            entity_type: "SERVICE_RECORD",
            entity_id: "SE-100",
            uploaded_at: "2026-04-15T10:00:00+00:00",
            file_size: 4096,
            is_locked: true,
          },
        ],
      },
    });
  });

  afterEach(() => {
    anchorClickSpy?.mockRestore();
  });

  test("uses ESS documents endpoint and performs preview and download actions", async () => {
    render(<EssDocumentsPage />);

    await waitFor(() => {
      expect(mockGetMyDocuments).toHaveBeenCalledTimes(1);
    });

    expect(mockGetMyDocuments).toHaveBeenCalledWith({
      query: undefined,
      document_type: undefined,
      source_context: undefined,
      is_locked: undefined,
      limit: 50,
      offset: 0,
    });

    expect(screen.getByTestId("ess-documents-page")).toBeInTheDocument();
    expect(screen.getByText("Appointment Order.pdf")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /preview/i }));

    await waitFor(() => {
      expect(mockPreviewMyDocument).toHaveBeenCalledWith("doc-1.pdf");
    });

    fireEvent.click(screen.getByRole("button", { name: /download/i }));

    await waitFor(() => {
      expect(mockDownloadMyDocument).toHaveBeenCalledWith("doc-1.pdf");
    });
  });

  test("hides preview action for non-previewable file types", async () => {
    mockGetMyDocuments.mockResolvedValueOnce({
      data: {
        total: 1,
        available_filters: {
          document_types: ["ORDER"],
          source_contexts: ["service_book.records.upload"],
        },
        items: [
          {
            document_id: "doc-2",
            filename: "doc-2.docx",
            original_name: "Office Note.docx",
            document_type: "ORDER",
            source_context: "service_book.records.upload",
            uploaded_at: "2026-04-15T10:00:00+00:00",
            file_size: 8192,
            is_locked: true,
            content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          },
        ],
      },
    });

    render(<EssDocumentsPage />);

    await waitFor(() => {
      expect(mockGetMyDocuments).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByRole("button", { name: /preview/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /download/i }));

    await waitFor(() => {
      expect(mockDownloadMyDocument).toHaveBeenCalledWith("doc-2.docx");
    });
  });
});
