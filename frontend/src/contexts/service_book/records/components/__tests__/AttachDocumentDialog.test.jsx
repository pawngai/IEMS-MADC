import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import AttachDocumentDialog from "@/contexts/service_book/records/components/AttachDocumentDialog";

const { toastError, toastSuccess, listDocuments, attachDocument, uploadDocument } = vi.hoisted(() => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
  listDocuments: vi.fn(),
  attachDocument: vi.fn(),
  uploadDocument: vi.fn(),
}));

vi.mock("@/contexts/service_book/records/api/serviceBookRecordsApi", () => ({
  serviceBookRecordsAPI: {
    attachDocument,
    listAccessibleDocuments: listDocuments,
    uploadLinkedDocument: uploadDocument,
  },
}));

vi.mock("@/shared/ui/sheet", () => ({
  __esModule: true,
  Sheet: ({ children }) => <div>{children}</div>,
  SheetContent: ({ children }) => <div>{children}</div>,
  SheetHeader: ({ children }) => <div>{children}</div>,
  SheetTitle: ({ children }) => <h2>{children}</h2>,
  SheetDescription: ({ children }) => <p>{children}</p>,
  SheetFooter: ({ children }) => <div>{children}</div>,
}));

vi.mock("sonner", () => ({
  toast: {
    error: toastError,
    success: toastSuccess,
  },
}));

describe("AttachDocumentDialog", () => {
  test("requires either an existing selection or a new upload", async () => {
    toastError.mockClear();
    listDocuments.mockResolvedValue({ data: { items: [] } });

    render(
      <AttachDocumentDialog
        event={{
          id: "c35c6d40-5d5e-4e60-80c2-5dc8559f5472",
          event_type: "PAY",
          payload: {
            remarks: "Annual increment for FY 2025-26",
          },
        }}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    await waitFor(() => expect(listDocuments).toHaveBeenCalled());
    fireEvent.submit(screen.getByRole("button", { name: "Attach Document" }).closest("form"));

    expect(toastError).toHaveBeenCalledWith("Select an existing document or upload a new one");
  });

  test("uses a readable event label and shows the picker flow", async () => {
    toastError.mockClear();
    listDocuments.mockResolvedValue({
      data: {
        items: [
          {
            document_id: "doc-1",
            filename: "doc-1.pdf",
            original_name: "Increment Order.pdf",
            document_type: "ORDER",
            category: "INCREMENT_ORDER",
            source_context: "change_requests.upload",
            uploaded_at: "2026-04-09T10:00:00+00:00",
          },
        ],
      },
    });

    render(
      <AttachDocumentDialog
        event={{
          id: "c35c6d40-5d5e-4e60-80c2-5dc8559f5472",
          event_type: "PAY",
          payload: {
            remarks: "Annual increment for FY 2025-26",
          },
        }}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    await waitFor(() => expect(listDocuments).toHaveBeenCalled());

    expect(
      screen.getByText(
        "Attach a supporting document to the increment event. Choose an existing document from your accessible uploads or upload a new one directly from this panel.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Choose Existing Document")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search by file name or document name")).toBeInTheDocument();
    expect(
      screen.getByText("Pick an existing document here, or leave this blank and upload a new one below."),
    ).toBeInTheDocument();
    expect(screen.getByText("Increment Order.pdf")).toBeInTheDocument();
    expect(screen.getByText("INCREMENT_ORDER")).toBeInTheDocument();
    expect(
      screen.queryByText(/c35c6d40-5d5e-4e60-80c2-5dc8559f5472/i),
    ).not.toBeInTheDocument();
  });

  test("attaches a selected existing document", async () => {
    const onSuccess = vi.fn();
    listDocuments.mockResolvedValue({
      data: {
        items: [
          {
            document_id: "doc-55",
            filename: "doc-55.pdf",
            original_name: "Promotion Order.pdf",
            document_type: "ORDER",
            source_context: "service_book.part_iia",
          },
        ],
      },
    });
    attachDocument.mockResolvedValue({ data: { success: true } });

    render(
      <AttachDocumentDialog
        event={{ id: "SE-55", event_type: "PROMOTION", payload: {} }}
        onSuccess={onSuccess}
        onClose={vi.fn()}
      />,
    );

    await waitFor(() => expect(screen.getByText("Promotion Order.pdf")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Promotion Order.pdf"));
    fireEvent.submit(screen.getByRole("button", { name: "Attach Document" }).closest("form"));

    await waitFor(() => {
      expect(attachDocument).toHaveBeenCalledWith("SE-55", {
        service_event_id: "SE-55",
        document_id: "doc-55",
        document_type: "ORDER",
      });
    });
    expect(onSuccess).toHaveBeenCalled();
  });

  test("uploads a new document and attaches it with service-record metadata", async () => {
    const onSuccess = vi.fn();
    listDocuments.mockResolvedValue({ data: { items: [] } });
    uploadDocument.mockResolvedValue({
      data: {
        document_id: "doc-uploaded-1",
        filename: "doc-uploaded-1.pdf",
        metadata: {
          document_type: "CERTIFICATE",
        },
      },
    });
    attachDocument.mockResolvedValue({ data: { success: true } });

    render(
      <AttachDocumentDialog
        event={{ id: "SE-77", event_type: "PROMOTION", payload: {} }}
        onSuccess={onSuccess}
        onClose={vi.fn()}
      />,
    );

    await waitFor(() => expect(listDocuments).toHaveBeenCalled());

    const file = new File(["%PDF-1.4"], "promotion-proof.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Upload New Document"), {
      target: { files: [file] },
    });
    fireEvent.change(screen.getByLabelText("Document Type"), {
      target: { value: "certificate" },
    });
    fireEvent.change(screen.getByLabelText("Category (optional)"), {
      target: { value: "promotion order" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Attach Document" }).closest("form"));

    await waitFor(() => {
      expect(uploadDocument).toHaveBeenCalledWith(file, {
        entity_type: "SERVICE_RECORD",
        entity_id: "SE-77",
        document_type: "CERTIFICATE",
        category: "PROMOTION_ORDER",
        source_context: "service_book.records.attach",
      });
    });

    expect(attachDocument).toHaveBeenCalledWith("SE-77", {
      service_event_id: "SE-77",
      document_id: "doc-uploaded-1",
      document_type: "CERTIFICATE",
    });
    expect(toastSuccess).toHaveBeenCalledWith("Document uploaded and attached");
    expect(onSuccess).toHaveBeenCalled();
  });
});